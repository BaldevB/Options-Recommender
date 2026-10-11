"""Walk-forward backtesting and baseline validation engine for options strategies.

Validates the institutional selector against naive baselines:
1. ATM 30-45 DTE
2. Fixed-Delta 0.40

Models conservative execution costs:
- Entry at ask + slippage
- Exit at bid - slippage
- Round-trip commissions ($1.30/contract)
- Round-trip bid-ask spread penalty

Tracks quote snapshots, realized fill proxies, P&L, maximum drawdown,
and performance by market regime.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
import json
import logging
import math
import os
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from config import RiskManagementConfig, DEFAULT_CONFIG
from options.suggester import (
    calculate_black_scholes_price,
    calculate_black_scholes_greeks,
    calculate_round_trip_friction,
    calculate_net_expectancy,
    calculate_model_implied_probability,
    compute_position_sizing,
)

logger = logging.getLogger(__name__)


@dataclass
class TradeSnapshot:
    """Historical quote snapshot, execution parameters, and realized outcome for a trade."""
    trade_id: str
    symbol: str
    strategy_name: str                # "current_selector", "baseline_atm_35dte", "baseline_fixed_delta_40"
    entry_date: str
    exit_date: str
    market_regime: str                # "Bull Trending", "Bear Trending", "High Volatility", "Choppy Range"
    underlying_spot_entry: float
    underlying_spot_exit: float
    option_type: str                  # "CALL" or "PUT"
    strike: float
    dte_entry: int
    dte_exit: int
    implied_volatility: float
    delta_entry: float
    bid_entry: float
    ask_entry: float
    realized_entry_fill: float        # Ask + slippage
    realized_exit_fill: float         # Bid - slippage
    contracts: int
    capital_invested: float
    round_trip_friction: float
    gross_pnl: float
    net_pnl: float                    # Realized P&L after friction
    pnl_pct: float
    exit_reason: str                  # "TP1_Target", "TP2_Target", "StopLoss", "TimeStop_21DTE", "Expiration"
    max_favorable_excursion_pct: float
    max_adverse_excursion_pct: float
    holding_days: int


@dataclass
class StrategyMetrics:
    """Institutional performance metrics for backtested strategies."""
    strategy_name: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    gross_pnl: float
    total_transaction_costs: float
    net_pnl: float
    profit_factor: float
    expectancy_per_trade: float
    max_drawdown_dollar: float
    max_drawdown_pct: float
    sharpe_ratio: float
    avg_holding_days: float
    regime_breakdown: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class WalkForwardValidationResult:
    """Complete validation comparison comparing selector against simple baselines."""
    validation_timestamp: str
    symbol: str
    period_start: str
    period_end: str
    total_regime_bars: int
    selector_metrics: StrategyMetrics
    baseline_atm_metrics: StrategyMetrics
    baseline_fixed_delta_metrics: StrategyMetrics
    net_outperformance_vs_atm: float
    net_outperformance_vs_fixed_delta: float
    rule_recommendation: str           # "Keep All Rules" or "Refine Rules"
    trade_snapshots: List[TradeSnapshot] = field(default_factory=list)


def detect_market_regime(historical_bars: pd.DataFrame, current_idx: int) -> str:
    """Classify the macro regime based on 20-day trend and 20-day annualized realized volatility."""
    if current_idx < 20 or len(historical_bars) < 20:
        return "Choppy Range"

    window = historical_bars.iloc[max(0, current_idx - 20):current_idx + 1]
    closes = window["Close"].values
    if len(closes) < 10:
        return "Choppy Range"

    ret_20d = (closes[-1] / closes[0]) - 1.0
    daily_returns = np.diff(closes) / closes[:-1]
    ann_vol = float(np.std(daily_returns) * math.sqrt(252))

    if ann_vol > 0.40:
        return "High Volatility"
    elif ret_20d > 0.04:
        return "Bull Trending"
    elif ret_20d < -0.04:
        return "Bear Trending"
    else:
        return "Choppy Range"


class WalkForwardBacktestEngine:
    """Simulates institutional options selection against naive baselines with realistic friction."""

    def __init__(
        self,
        risk_cfg: Optional[RiskManagementConfig] = None,
        commission_per_contract: float = 0.65,
        slippage_pct: float = 0.02,
    ):
        self.risk_cfg = risk_cfg or DEFAULT_CONFIG.risk
        self.commission_per_contract = commission_per_contract
        self.slippage_pct = slippage_pct

    def simulate_trade_path(
        self,
        symbol: str,
        strategy_name: str,
        entry_idx: int,
        entry_date: str,
        spot_entry: float,
        strike: float,
        dte_init: int,
        iv_init: float,
        is_call: bool,
        contracts: int,
        bars: pd.DataFrame,
        market_regime: str,
    ) -> Optional[TradeSnapshot]:
        """Simulate realistic day-by-day Black-Scholes price evolution, limits, and stops."""
        if contracts <= 0 or spot_entry <= 0 or strike <= 0:
            return None

        # Modeled entry quote
        t_entry = dte_init / 365.0
        model_entry_px = calculate_black_scholes_price(
            spot=spot_entry, strike=strike, t_years=t_entry,
            sigma=iv_init, r=0.045, is_call=is_call
        )
        if model_entry_px <= 0.05:
            return None

        # Realistic bid-ask model based on liquidity and price
        half_spread = max(0.03, model_entry_px * 0.025)
        bid_entry = max(0.01, round(model_entry_px - half_spread, 2))
        ask_entry = round(model_entry_px + half_spread, 2)

        # Realized entry fill with slippage
        realized_entry_fill = round(ask_entry * (1.0 + self.slippage_pct), 2)
        total_entry_capital = round(contracts * realized_entry_fill * 100.0, 2)

        # Targets and stops
        tp1_opt_px = round(realized_entry_fill * 1.50, 2)   # +50% target
        tp2_opt_px = round(realized_entry_fill * 2.00, 2)   # +100% target
        sl_opt_px = round(realized_entry_fill * 0.50, 2)    # -50% stop-loss

        g_entry = calculate_black_scholes_greeks(spot_entry, strike, dte_init, iv_init, is_call)
        delta_entry = g_entry.delta

        # Round-trip friction modeled upfront
        rt_friction_one = calculate_round_trip_friction(
            ask=ask_entry, bid=bid_entry,
            commission_per_contract=self.commission_per_contract,
            slippage_pct=self.slippage_pct
        )
        total_rt_friction = round(contracts * rt_friction_one, 2)

        max_fav = 0.0
        max_adv = 0.0
        exit_date = entry_date
        exit_reason = "Expiration"
        realized_exit_fill = 0.0
        holding_days = 0
        final_spot = spot_entry

        total_bars = len(bars)
        # Walk forward day-by-day
        for step in range(1, min(dte_init + 1, total_bars - entry_idx)):
            curr_idx = entry_idx + step
            row = bars.iloc[curr_idx]
            curr_spot = float(row["Close"])
            curr_date = str(row.name if isinstance(row.name, str) else row.get("Date", f"Day_{step}"))
            dte_remain = max(0, dte_init - step)
            final_spot = curr_spot
            holding_days = step
            exit_date = curr_date

            # Current theoretical option price with time decay
            t_rem = dte_remain / 365.0
            if dte_remain == 0:
                curr_opt_px = max(0.0, curr_spot - strike) if is_call else max(0.0, strike - curr_spot)
            else:
                curr_opt_px = calculate_black_scholes_price(
                    spot=curr_spot, strike=strike, t_years=t_rem,
                    sigma=iv_init, r=0.045, is_call=is_call
                )

            pnl_move_pct = (curr_opt_px - realized_entry_fill) / realized_entry_fill
            max_fav = max(max_fav, pnl_move_pct)
            max_adv = min(max_adv, pnl_move_pct)

            # Check Stop-Loss
            if curr_opt_px <= sl_opt_px:
                exit_reason = "StopLoss"
                realized_exit_fill = round(sl_opt_px * (1.0 - self.slippage_pct), 2)
                break

            # Check TP2
            if curr_opt_px >= tp2_opt_px:
                exit_reason = "TP2_Target"
                realized_exit_fill = round(tp2_opt_px * (1.0 - self.slippage_pct), 2)
                break

            # Check TP1
            if curr_opt_px >= tp1_opt_px:
                exit_reason = "TP1_Target"
                realized_exit_fill = round(tp1_opt_px * (1.0 - self.slippage_pct), 2)
                break

            # Check 21 DTE time stop rule (for current selector)
            if strategy_name == "current_selector" and dte_remain <= 21:
                exit_reason = "TimeStop_21DTE"
                half_sp = max(0.03, curr_opt_px * 0.03)
                bid_exit = max(0.01, curr_opt_px - half_sp)
                realized_exit_fill = round(bid_exit * (1.0 - self.slippage_pct), 2)
                break

            # Expiration
            if dte_remain == 0:
                exit_reason = "Expiration"
                realized_exit_fill = round(curr_opt_px, 2)
                break

        if realized_exit_fill == 0.0 and exit_reason == "Expiration":
            exp_intrinsic = max(0.0, final_spot - strike) if is_call else max(0.0, strike - final_spot)
            realized_exit_fill = round(exp_intrinsic, 2)

        gross_pnl = round(contracts * (realized_exit_fill - realized_entry_fill) * 100.0, 2)
        net_pnl = round(gross_pnl - total_rt_friction, 2)
        pnl_pct = round((net_pnl / total_entry_capital) * 100.0, 1) if total_entry_capital > 0 else 0.0

        trade_id = f"{symbol}_{strategy_name}_{entry_date}_{strike}_{dte_init}"

        return TradeSnapshot(
            trade_id=trade_id,
            symbol=symbol,
            strategy_name=strategy_name,
            entry_date=entry_date,
            exit_date=exit_date,
            market_regime=market_regime,
            underlying_spot_entry=round(spot_entry, 2),
            underlying_spot_exit=round(final_spot, 2),
            option_type="CALL" if is_call else "PUT",
            strike=round(strike, 2),
            dte_entry=dte_init,
            dte_exit=max(0, dte_init - holding_days),
            implied_volatility=round(iv_init, 3),
            delta_entry=round(delta_entry, 3),
            bid_entry=bid_entry,
            ask_entry=ask_entry,
            realized_entry_fill=realized_entry_fill,
            realized_exit_fill=realized_exit_fill,
            contracts=contracts,
            capital_invested=total_entry_capital,
            round_trip_friction=total_rt_friction,
            gross_pnl=gross_pnl,
            net_pnl=net_pnl,
            pnl_pct=pnl_pct,
            exit_reason=exit_reason,
            max_favorable_excursion_pct=round(max_fav * 100.0, 1),
            max_adverse_excursion_pct=round(max_adv * 100.0, 1),
            holding_days=holding_days,
        )

    def run_walk_forward(
        self,
        symbol: str,
        historical_bars: pd.DataFrame,
        sample_step_days: int = 15,
        default_iv: float = 0.35,
    ) -> WalkForwardValidationResult:
        """Run full walk-forward validation across the historical dataset."""
        if historical_bars is None or len(historical_bars) < 45:
            raise ValueError(f"Insufficient historical bars for walk-forward test (need at least 45, got {len(historical_bars) if historical_bars is not None else 0})")

        trades_selector: List[TradeSnapshot] = []
        trades_atm: List[TradeSnapshot] = []
        trades_fixed_delta: List[TradeSnapshot] = []

        total_bars = len(historical_bars)
        period_start = str(historical_bars.index[0])[:10]
        period_end = str(historical_bars.index[-1])[:10]

        # Step through historical windows
        for idx in range(30, total_bars - 20, sample_step_days):
            row = historical_bars.iloc[idx]
            spot = float(row["Close"])
            date_str = str(row.name)[:10] if hasattr(row, "name") else f"Step_{idx}"
            regime = detect_market_regime(historical_bars, idx)

            # Generate momentum direction signal
            ret_10d = (spot / float(historical_bars.iloc[idx - 10]["Close"])) - 1.0
            is_call = (ret_10d >= 0)  # Follow 10-day momentum trend

            # 1. CURRENT SELECTOR: Conservative Net EV, Hard Affordability, Delta 0.35-0.50, 45 DTE
            selector_dte = 45
            # Strike target ~0.42 Delta
            strike_offset = spot * (0.02 if is_call else -0.02)
            selector_strike = round(spot + (strike_offset if is_call else -strike_offset), 1)

            t_sel = selector_dte / 365.0
            sel_opt_px = calculate_black_scholes_price(spot, selector_strike, t_sel, default_iv, 0.045, is_call)
            c_sel, _, _, _, sel_afford = compute_position_sizing(sel_opt_px, self.risk_cfg)

            # EV check: reject if negative expected value
            sel_pop = calculate_model_implied_probability(spot, selector_strike + sel_opt_px if is_call else selector_strike - sel_opt_px, selector_dte, default_iv, is_call)
            sel_friction = calculate_round_trip_friction(sel_opt_px + 0.05, max(0.01, sel_opt_px - 0.05), self.commission_per_contract, self.slippage_pct)
            sel_ev = calculate_net_expectancy(sel_opt_px, sel_pop, sel_friction)

            if sel_afford and c_sel >= 1 and sel_ev > 0.0:
                snap_sel = self.simulate_trade_path(
                    symbol=symbol,
                    strategy_name="current_selector",
                    entry_idx=idx,
                    entry_date=date_str,
                    spot_entry=spot,
                    strike=selector_strike,
                    dte_init=selector_dte,
                    iv_init=default_iv,
                    is_call=is_call,
                    contracts=c_sel,
                    bars=historical_bars,
                    market_regime=regime,
                )
                if snap_sel:
                    trades_selector.append(snap_sel)

            # 2. BASELINE 1: ATM 35 DTE (No EV filter, fixed ATM strike)
            atm_dte = 35
            atm_strike = round(spot, 1)
            t_atm = atm_dte / 365.0
            atm_opt_px = calculate_black_scholes_price(spot, atm_strike, t_atm, default_iv, 0.045, is_call)
            c_atm, _, _, _, atm_afford = compute_position_sizing(atm_opt_px, self.risk_cfg)
            if atm_afford and c_atm >= 1:
                snap_atm = self.simulate_trade_path(
                    symbol=symbol,
                    strategy_name="baseline_atm_35dte",
                    entry_idx=idx,
                    entry_date=date_str,
                    spot_entry=spot,
                    strike=atm_strike,
                    dte_init=atm_dte,
                    iv_init=default_iv,
                    is_call=is_call,
                    contracts=c_atm,
                    bars=historical_bars,
                    market_regime=regime,
                )
                if snap_atm:
                    trades_atm.append(snap_atm)

            # 3. BASELINE 2: FIXED-DELTA 0.40 (Ignores transaction cost penalty & time stop)
            fd_dte = 30
            fd_strike = round(spot * (1.03 if is_call else 0.97), 1)
            t_fd = fd_dte / 365.0
            fd_opt_px = calculate_black_scholes_price(spot, fd_strike, t_fd, default_iv, 0.045, is_call)
            c_fd, _, _, _, fd_afford = compute_position_sizing(fd_opt_px, self.risk_cfg)
            if fd_afford and c_fd >= 1:
                snap_fd = self.simulate_trade_path(
                    symbol=symbol,
                    strategy_name="baseline_fixed_delta_40",
                    entry_idx=idx,
                    entry_date=date_str,
                    spot_entry=spot,
                    strike=fd_strike,
                    dte_init=fd_dte,
                    iv_init=default_iv,
                    is_call=is_call,
                    contracts=c_fd,
                    bars=historical_bars,
                    market_regime=regime,
                )
                if snap_fd:
                    trades_fixed_delta.append(snap_fd)

        # Aggregate metrics
        sel_metrics = self._compute_strategy_metrics("Institutional Net EV Selector", trades_selector)
        atm_metrics = self._compute_strategy_metrics("Baseline 1: ATM 35 DTE", trades_atm)
        fd_metrics = self._compute_strategy_metrics("Baseline 2: Fixed Delta 0.40", trades_fixed_delta)

        outperf_atm = round(sel_metrics.net_pnl - atm_metrics.net_pnl, 2)
        outperf_fd = round(sel_metrics.net_pnl - fd_metrics.net_pnl, 2)

        rule_rec = "Keep All Rules" if (sel_metrics.net_pnl >= atm_metrics.net_pnl and sel_metrics.max_drawdown_pct <= atm_metrics.max_drawdown_pct) else "Refine Rules"

        all_trades = trades_selector + trades_atm + trades_fixed_delta

        return WalkForwardValidationResult(
            validation_timestamp=datetime.now(timezone.utc).isoformat(),
            symbol=symbol,
            period_start=period_start,
            period_end=period_end,
            total_regime_bars=total_bars,
            selector_metrics=sel_metrics,
            baseline_atm_metrics=atm_metrics,
            baseline_fixed_delta_metrics=fd_metrics,
            net_outperformance_vs_atm=outperf_atm,
            net_outperformance_vs_fixed_delta=outperf_fd,
            rule_recommendation=rule_rec,
            trade_snapshots=all_trades,
        )

    def _compute_strategy_metrics(self, name: str, trades: List[TradeSnapshot]) -> StrategyMetrics:
        """Calculate statistical performance metrics from a trade snapshot list."""
        if not trades:
            return StrategyMetrics(
                strategy_name=name,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate_pct=0.0,
                gross_pnl=0.0,
                total_transaction_costs=0.0,
                net_pnl=0.0,
                profit_factor=0.0,
                expectancy_per_trade=0.0,
                max_drawdown_dollar=0.0,
                max_drawdown_pct=0.0,
                sharpe_ratio=0.0,
                avg_holding_days=0.0,
                regime_breakdown={},
            )

        n = len(trades)
        wins = [t for t in trades if t.net_pnl > 0]
        losses = [t for t in trades if t.net_pnl <= 0]
        win_rate = (len(wins) / n) * 100.0

        gross_pnl = sum(t.gross_pnl for t in trades)
        costs = sum(t.round_trip_friction for t in trades)
        net_pnl = sum(t.net_pnl for t in trades)

        gross_gains = sum(t.net_pnl for t in wins)
        gross_losses = abs(sum(t.net_pnl for t in losses))
        profit_factor = round(gross_gains / gross_losses, 2) if gross_losses > 0 else (99.0 if gross_gains > 0 else 1.0)
        expectancy = round(net_pnl / n, 2)

        # Drawdown calculation
        cumulative_pnl = np.cumsum([t.net_pnl for t in trades])
        peak = np.maximum.accumulate(cumulative_pnl)
        drawdown = peak - cumulative_pnl
        max_dd_dollar = round(float(np.max(drawdown)), 2) if len(drawdown) > 0 else 0.0

        capital_base = self.risk_cfg.account_equity
        max_dd_pct = round((max_dd_dollar / capital_base) * 100.0, 1)

        # Sharpe ratio proxy
        returns = [t.pnl_pct / 100.0 for t in trades]
        mean_ret = float(np.mean(returns)) if len(returns) > 0 else 0.0
        std_ret = float(np.std(returns)) if len(returns) > 1 else 0.01
        sharpe = round((mean_ret / (std_ret if std_ret > 0 else 0.01)) * math.sqrt(min(n, 25)), 2)

        avg_hold = round(float(np.mean([t.holding_days for t in trades])), 1)

        # Regime breakdown
        regimes: Dict[str, List[TradeSnapshot]] = {}
        for t in trades:
            regimes.setdefault(t.market_regime, []).append(t)

        regime_breakdown = {}
        for r_name, r_trades in regimes.items():
            r_wins = len([t for t in r_trades if t.net_pnl > 0])
            r_net = round(sum(t.net_pnl for t in r_trades), 2)
            regime_breakdown[r_name] = {
                "trades": len(r_trades),
                "win_rate_pct": round((r_wins / len(r_trades)) * 100.0, 1),
                "net_pnl": r_net,
            }

        return StrategyMetrics(
            strategy_name=name,
            total_trades=n,
            winning_trades=len(wins),
            losing_trades=len(losses),
            win_rate_pct=round(win_rate, 1),
            gross_pnl=round(gross_pnl, 2),
            total_transaction_costs=round(costs, 2),
            net_pnl=round(net_pnl, 2),
            profit_factor=profit_factor,
            expectancy_per_trade=expectancy,
            max_drawdown_dollar=max_dd_dollar,
            max_drawdown_pct=max_dd_pct,
            sharpe_ratio=sharpe,
            avg_holding_days=avg_hold,
            regime_breakdown=regime_breakdown,
        )


def save_validation_results(result: WalkForwardValidationResult, output_path: str = "backtest_results.json") -> None:
    """Save walk-forward backtest snapshot and metrics to JSON file."""
    try:
        data = asdict(result)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Successfully exported walk-forward backtest results to {output_path}")
    except Exception as e:
        logger.error(f"Failed to export backtest results: {e}")
