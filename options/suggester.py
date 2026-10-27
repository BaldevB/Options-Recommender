"""Options contract filtering, Black-Scholes Delta calculation, debit spread generation, position sizing, and institutional trade plans."""

from dataclasses import dataclass, field
import logging
import math
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from analysis.signals import TradeSignal, BiasDirection
from config import (
    OptionsFilterConfig, HighRiskOptionsFilterConfig, ZeroDteOptionsFilterConfig, RiskManagementConfig,
    DEFAULT_CONFIG
)

logger = logging.getLogger(__name__)


@dataclass
class OptionTradePlan:
    """Comprehensive institutional trade plan for execution, profit taking, and risk control."""
    entry_limit_price: float              # Favorable limit entry (mid-price)
    entry_market_price: float             # Market ask price
    entry_zone: str                       # e.g. "$2.40 – $2.55"
    underlying_spot: float                # Spot price at signal
    underlying_invalidation_price: float  # Key chart invalidation level on underlying
    # Take Profit Targets
    tp1_option_price: float               # +50% target on option premium
    tp1_dollar_gain: float                # Gain per contract at TP1 ($)
    tp1_underlying_target: float          # Underlying target price for TP1 ($)
    tp1_gain_pct: float                   # +50.0%
    tp1_action: str                       # "Trim 50% contracts & move stop to Breakeven"
    tp2_option_price: float               # +100% target on option premium
    tp2_dollar_gain: float                # Gain per contract at TP2 ($)
    tp2_underlying_target: float          # Underlying target price for TP2 ($)
    tp2_gain_pct: float                   # +100.0%
    tp2_action: str                       # "Sell 30-50% contracts, trail remainder"
    tp3_runner_price: float               # +150% runner target on option premium
    tp3_dollar_gain: float                # Gain per contract at TP3 ($)
    tp3_underlying_target: float          # Underlying target price for TP3 ($)
    tp3_gain_pct: float                   # +150.0%
    tp3_action: str                       # "Trail remaining runner along 8-day EMA"
    # Stop-Loss Plan
    stop_loss_option_price: float         # 50% stop loss on option premium
    stop_loss_dollar_loss: float          # Max loss per contract at 50% stop ($)
    total_planned_risk: float             # Planned dollar risk (contracts * stop_loss_dollar_loss)
    max_capital_loss: float               # Total capital at risk if option goes to $0
    stop_loss_rule: str                   # Detailed stop loss execution rule
    # Time Stop & Theta Defense
    daily_theta_decay: float              # Daily decay in $ per contract
    max_holding_period_days: int          # Recommended max holding duration (days)
    time_stop_rule: str                   # Time-stop defense rule (e.g. 21 DTE rule)
    # Edge & Analytics
    probability_of_profit_pct: float      # Analytical Probability of Profit (%)
    risk_reward_ratio: float              # TP2 gain vs Stop Loss risk
    expected_value_per_contract: float    # Expected dollar value per contract
    # Execution Checklist Playbook
    playbook_steps: List[str] = field(default_factory=list)
    # Phase 1: Dynamic Trade Management
    ratchet_ladder: List[Dict[str, Any]] = field(default_factory=list)
    rolling_playbook: Dict[str, Any] = field(default_factory=dict)
    broker_bracket_order: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OptionSuggestion:
    """Detailed recommendation for a single-leg options contract with risk management."""
    contract_symbol: str
    option_type: str                  # "CALL" or "PUT"
    strike: float
    expiration: str
    dte: int
    spot_price: float
    bid: float
    ask: float
    mid_price: float
    spread: float
    spread_pct_of_mid: float
    volume: int
    open_interest: int
    implied_volatility_pct: float
    delta: float                      # Black-Scholes Delta
    moneyness_pct: float              # (strike / spot - 1) * 100
    in_the_money: bool
    breakeven_price: float
    required_move_pct: float
    rank_score: float
    # Risk Management & Position Sizing
    max_loss_per_contract: float      # Premium * 100
    suggested_contracts: int          # Sized based on account equity & risk %
    total_dollar_risk: float          # Suggested contracts * max loss
    suggested_stop_loss_price: float  # Option exit price (50% stop)
    stop_loss_dollar_risk: float      # Max loss at 50% stop
    gamma: float = 0.0                # Black-Scholes Gamma
    theta: float = 0.0                # Black-Scholes Theta ($/day decay)
    vega: float = 0.0                 # Black-Scholes Vega ($/1% IV shift)
    risk_warnings: List[str] = field(default_factory=list)
    trade_plan: Optional[OptionTradePlan] = None


@dataclass
class DebitSpreadSuggestion:
    """Vertical debit spread recommendation for high-IV or defined-risk environments."""
    spread_type: str                  # "Bull Call Spread" or "Bear Put Spread"
    expiration: str
    dte: int
    long_contract: str
    long_strike: float
    long_ask: float
    long_delta: float
    short_contract: str
    short_strike: float
    short_bid: float
    short_delta: float
    net_debit: float                  # Cost per share
    max_loss_per_contract: float      # Net debit * 100
    max_profit_per_contract: float    # (Width - Net debit) * 100
    breakeven_price: float
    risk_reward_ratio: float          # Max Profit / Max Loss
    suggested_contracts: int
    total_dollar_risk: float
    spread_notes: str
    trade_plan: Optional[Dict[str, Any]] = None


@dataclass
class HighRiskTradeSetup:
    """Aggressive, asymmetric high-risk options trade setup (Moonshot / High Gamma)."""
    setup_name: str                   # e.g. "Asymmetric Moonshot Call"
    contract_symbol: str
    option_type: str                  # "CALL" or "PUT"
    strike: float
    expiration: str
    dte: int
    bid: float
    ask: float
    delta: float                      # 0.15 to 0.28 Delta
    moneyness_pct: float              # % OTM
    breakeven_price: float
    required_move_pct: float
    upside_leverage: float            # Potential payoff ratio on a 10% move
    suggested_contracts: int          # Sized with trade risk budget (uncapped)
    total_dollar_risk: float
    lotto_spread: Optional[DebitSpreadSuggestion] = None
    risk_warnings: List[str] = field(default_factory=list)
    trade_plan: Optional[Dict[str, Any]] = None


@dataclass
class ZeroDteTradeSetup:
    """High-velocity 0DTE (same-day / front-session) options trade setup."""
    symbol: str
    spot_price: float
    bias: str
    expiration: str
    dte: int
    # 1. ATM / Near-ATM Momentum Scalp Setup (~0.45-0.55 Delta)
    scalp_contract: str
    scalp_strike: float
    scalp_type: str
    scalp_bid: float
    scalp_ask: float
    scalp_delta: float
    scalp_gamma: float
    scalp_theta: float
    scalp_theta_per_hour: float
    scalp_suggested_contracts: int
    scalp_total_risk: float
    scalp_breakeven: float
    scalp_req_move_pct: float
    # 2. OTM Lotto Gamma Moonshot Setup (~0.15-0.28 Delta)
    lotto_contract: str
    lotto_strike: float
    lotto_bid: float
    lotto_ask: float
    lotto_delta: float
    lotto_gamma: float
    lotto_upside_leverage: float
    lotto_suggested_contracts: int
    lotto_total_risk: float
    lotto_breakeven: float
    lotto_req_move_pct: float
    # 3. Asymmetric 0DTE Lotto Debit Spread
    lotto_spread: Optional[DebitSpreadSuggestion] = None
    # Intraday Velocity & Risk Analytics
    breakeven_velocity_per_hour: float = 0.0
    risk_warnings: List[str] = field(default_factory=list)
    trade_plan: Optional[Dict[str, Any]] = None


@dataclass
class ScreeningResult:
    """Encapsulates single-leg suggestions, debit spread alternatives, and audit diagnostics."""
    single_leg_suggestions: List[OptionSuggestion] = field(default_factory=list)
    spread_suggestions: List[DebitSpreadSuggestion] = field(default_factory=list)
    high_risk_setup: Optional[HighRiskTradeSetup] = None
    zero_dte_setup: Optional[ZeroDteTradeSetup] = None
    elevated_iv: bool = False
    avg_iv_pct: float = 0.0
    audit_log: Dict[str, int] = field(default_factory=dict)


@dataclass
class OptionGreeks:
    """Complete Black-Scholes Greeks."""
    delta: float
    gamma: float
    theta: float  # Dollar decay per day per share
    vega: float   # Dollar change per 1% IV change per share
    rho: float    # Dollar change per 1% interest rate change per share


def calculate_black_scholes_greeks(
    spot: float,
    strike: float,
    dte: int,
    iv: float,
    is_call: bool,
    risk_free_rate: float = 0.045
) -> OptionGreeks:
    """Calculate complete Black-Scholes Greeks (Delta, Gamma, Theta, Vega, Rho)."""
    if spot <= 0 or strike <= 0 or dte < 0:
        return OptionGreeks(
            delta=0.50 if is_call else -0.50,
            gamma=0.0,
            theta=0.0,
            vega=0.0,
            rho=0.0
        )

    t = max((dte if dte > 0 else 0.5) / 365.0, 0.0005)
    sigma = max(iv, 0.05)
    r = risk_free_rate

    try:
        d1 = (math.log(spot / strike) + (r + 0.5 * (sigma ** 2)) * t) / (sigma * math.sqrt(t))
        d2 = d1 - sigma * math.sqrt(t)

        norm_cdf_d1 = 0.5 * (1.0 + math.erf(d1 / math.sqrt(2.0)))
        norm_cdf_d2 = 0.5 * (1.0 + math.erf(d2 / math.sqrt(2.0)))
        norm_pdf_d1 = (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * (d1 ** 2))

        # Delta
        delta = norm_cdf_d1 if is_call else (norm_cdf_d1 - 1.0)

        # Gamma (identical for Call and Put)
        gamma = norm_pdf_d1 / (spot * sigma * math.sqrt(t))

        # Theta (1-day decay in $ per share)
        term1 = -(spot * norm_pdf_d1 * sigma) / (2.0 * math.sqrt(t))
        if is_call:
            term2 = -r * strike * math.exp(-r * t) * norm_cdf_d2
        else:
            term2 = r * strike * math.exp(-r * t) * (1.0 - norm_cdf_d2)
        theta = (term1 + term2) / 365.0

        # Vega ($ change per 1% IV shift)
        vega = (spot * math.sqrt(t) * norm_pdf_d1) / 100.0

        # Rho ($ change per 1% interest rate shift)
        if is_call:
            rho = (strike * t * math.exp(-r * t) * norm_cdf_d2) / 100.0
        else:
            rho = (-strike * t * math.exp(-r * t) * (1.0 - norm_cdf_d2)) / 100.0

        return OptionGreeks(
            delta=round(delta, 3),
            gamma=round(gamma, 4),
            theta=round(theta, 3),
            vega=round(vega, 3),
            rho=round(rho, 4)
        )
    except Exception:
        moneyness = spot / strike
        approx_delta = (
            (0.65 if moneyness > 1.05 else (0.50 if moneyness > 0.98 else 0.35))
            if is_call else
            (-0.35 if moneyness > 1.02 else (-0.50 if moneyness > 0.95 else -0.65))
        )
        return OptionGreeks(
            delta=round(approx_delta, 3),
            gamma=0.01,
            theta=-0.05,
            vega=0.05,
            rho=0.01
        )


def calculate_black_scholes_delta(
    spot: float,
    strike: float,
    dte: int,
    iv: float,
    is_call: bool,
    risk_free_rate: float = 0.045
) -> float:
    """Calculate Black-Scholes Delta using standard error function (zero external dependencies)."""
    return calculate_black_scholes_greeks(spot, strike, dte, iv, is_call, risk_free_rate).delta


def calculate_probability_of_profit(
    spot: float,
    breakeven: float,
    dte: int,
    iv: float,
    is_call: bool,
    risk_free_rate: float = 0.045
) -> float:
    """Calculate Probability of Profit (PoP %) at expiration based on Black-Scholes N(d2)."""
    if spot <= 0 or breakeven <= 0:
        return 50.0
    t = max((dte if dte > 0 else 0.5) / 365.0, 0.0005)
    sigma = max(iv, 0.05)
    r = risk_free_rate
    try:
        d2 = (math.log(spot / breakeven) + (r - 0.5 * (sigma ** 2)) * t) / (sigma * math.sqrt(t))
        pop = 0.5 * (1.0 + math.erf(d2 / math.sqrt(2.0))) if is_call else 0.5 * (1.0 - math.erf(d2 / math.sqrt(2.0)))
        return round(float(np.clip(pop * 100.0, 5.0, 95.0)), 1)
    except Exception:
        return 50.0


def build_option_trade_plan(
    spot_price: float,
    strike: float,
    bid: float,
    ask: float,
    mid_price: float,
    delta: float,
    gamma: float,
    theta: float,
    dte: int,
    iv_pct: float,
    is_call: bool,
    contracts: int,
    total_dollar_risk: float,
    stop_loss_px: float,
    stop_loss_dollar: float,
    breakeven_px: float,
    contract_symbol: str = "",
) -> OptionTradePlan:
    """Build a complete, disciplined institutional trade plan for an options position."""
    entry_mid = round(max(mid_price, 0.05), 2)
    entry_ask = round(max(ask, 0.05), 2)
    entry_zone = f"${entry_mid:.2f} – ${entry_ask:.2f}"
    abs_delta = max(abs(delta), 0.15)

    # 1. Target 1 (+50% option gain)
    tp1_opt_px = round(entry_mid * 1.50, 2)
    tp1_gain = round((tp1_opt_px - entry_mid) * 100.0, 2)
    delta_move_1 = (tp1_opt_px - entry_mid) / abs_delta
    tp1_underlying = round(spot_price + delta_move_1 if is_call else spot_price - delta_move_1, 2)
    tp1_action = f"Trim 50% of contracts at ${tp1_opt_px:.2f} (+50%) to lock gains; move stop loss on remaining to Breakeven (${entry_mid:.2f})."

    # 2. Target 2 (+100% option gain / Core Target)
    tp2_opt_px = round(entry_mid * 2.00, 2)
    tp2_gain = round((tp2_opt_px - entry_mid) * 100.0, 2)
    eff_delta_2 = min(abs_delta + 0.12, 0.85)  # Account for gamma expansion
    delta_move_2 = (tp2_opt_px - entry_mid) / eff_delta_2
    tp2_underlying = round(spot_price + delta_move_2 if is_call else spot_price - delta_move_2, 2)
    tp2_action = f"Take profit on 30–50% of position at ${tp2_opt_px:.2f} (+100%); let remaining runners ride with trailing stop."

    # 3. Target 3 (+150% runner target)
    tp3_opt_px = round(entry_mid * 2.50, 2)
    tp3_gain = round((tp3_opt_px - entry_mid) * 100.0, 2)
    eff_delta_3 = min(abs_delta + 0.20, 0.95)
    delta_move_3 = (tp3_opt_px - entry_mid) / eff_delta_3
    tp3_underlying = round(spot_price + delta_move_3 if is_call else spot_price - delta_move_3, 2)
    tp3_action = "Trail final contracts along 8-day EMA on daily chart until trend breakdown."

    # 4. Stop-loss & Invalidation
    sl_opt_px = round(entry_mid * 0.50, 2)
    sl_dollar = round((entry_mid - sl_opt_px) * 100.0, 2)
    planned_risk = round(contracts * sl_dollar, 2)
    max_capital = round(contracts * entry_ask * 100.0, 2)

    delta_move_sl = (entry_mid - sl_opt_px) / abs_delta
    underlying_inval = round(spot_price - delta_move_sl if is_call else spot_price + delta_move_sl, 2)
    stop_rule = (
        f"Execute hard exit if option drops to ${sl_opt_px:.2f} (-50% premium loss) "
        f"OR if underlying closes beyond ${underlying_inval:.2f}."
    )

    # 5. Probability of Profit (PoP %)
    pop_pct = calculate_probability_of_profit(
        spot=spot_price,
        breakeven=breakeven_px,
        dte=dte,
        iv=iv_pct / 100.0,
        is_call=is_call
    )

    # 6. Risk-to-Reward
    rr_ratio = round(tp2_gain / sl_dollar, 2) if sl_dollar > 0 else 2.0

    # 7. Expected Value ($/contract)
    p_win = pop_pct / 100.0
    p_loss = 1.0 - p_win
    ev_val = round((p_win * tp1_gain) - (p_loss * sl_dollar), 2)

    # 8. Theta & Time Stop
    daily_theta_dollar = round(abs(theta) * 100.0, 2) if theta != 0.0 else round(entry_mid * 0.03 * 100.0, 2)
    max_hold_days = min(12, max(3, dte - 14))
    time_rule = (
        f"Close trade if underlying stalls after {max_hold_days} trading days or when contract reaches 21 DTE "
        f"to prevent severe theta decay acceleration (decay: -${daily_theta_dollar:.2f}/contract/day)."
    )

    # 9. Playbook steps
    playbook_steps = [
        f"1. Entry: Limit order at mid-price ${entry_mid:.2f} (entry zone {entry_zone}). Do not chase ask at ${entry_ask:.2f}.",
        f"2. De-Risk (TP1): At ${tp1_opt_px:.2f} (+50%), sell 50% contracts and move stop loss on remainder to Breakeven (${entry_mid:.2f}).",
        f"3. Core Target (TP2): At ${tp2_opt_px:.2f} (+100%), take profit on 30-50% contracts; trail remaining runners with 8-EMA.",
        f"4. Hard Stop: Exit if option falls to ${sl_opt_px:.2f} (-50%) or underlying daily close breaches ${underlying_inval:.2f}.",
        f"5. Time Stop: Close position if trade stalls after {max_hold_days} days or reaches 21 DTE to defend against theta decay."
    ]

    # Phase 1: Dynamic Ratchet Stop Ladder (Phases 1 - 4)
    ratchet_ladder = [
        {
            "stage_num": 1,
            "phase": "Phase 1: Initial Entry & Capital Protection",
            "trigger_condition": f"At Entry (${entry_mid:.2f} Mid)",
            "stop_level_option": sl_opt_px,
            "stop_level_stock": underlying_inval,
            "stop_rule_label": f"${sl_opt_px:.2f} (-50% Stop)",
            "risk_state": "Full Planned Risk",
            "risk_badge": "bg-red-500/20 text-red-300 border-red-500/30",
            "locked_profit": f"-$0.00 (Max Planned Risk: -${sl_dollar:.0f}/ct)",
            "action": f"Hard stop active at ${sl_opt_px:.2f}. Cut if stock candle closes beyond ${underlying_inval:.2f}.",
            "is_active_initial": True,
        },
        {
            "stage_num": 2,
            "phase": "Phase 2: Breakeven De-Risk (Post-TP1)",
            "trigger_condition": f"Option hits TP1 ${tp1_opt_px:.2f} (+50%) / Stock ~${tp1_underlying:.2f}",
            "stop_level_option": entry_mid,
            "stop_level_stock": round(spot_price, 2),
            "stop_rule_label": f"${entry_mid:.2f} (Breakeven)",
            "risk_state": "Risk-Free Trade",
            "risk_badge": "bg-cyan-500/20 text-cyan-300 border-cyan-500/30",
            "locked_profit": f"+${tp1_gain * 0.5:.0f}/ct net bank realized",
            "action": f"Trim 50% position. Ratchet stop on remaining contracts up to Breakeven (${entry_mid:.2f}). Zero principal at risk.",
            "is_active_initial": False,
        },
        {
            "stage_num": 3,
            "phase": "Phase 3: Profit Floor Lock (Post-TP2)",
            "trigger_condition": f"Option hits TP2 ${tp2_opt_px:.2f} (+100%) / Stock ~${tp2_underlying:.2f}",
            "stop_level_option": tp1_opt_px,
            "stop_level_stock": tp1_underlying,
            "stop_rule_label": f"${tp1_opt_px:.2f} (+50% Profit Floor)",
            "risk_state": "Guaranteed Profit Floor",
            "risk_badge": "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
            "locked_profit": f"+${(tp1_gain * 0.5) + (tp2_gain * 0.3):.0f}/ct guaranteed gain",
            "action": f"Sell 30-50% position at +100%. Move stop floor up to ${tp1_opt_px:.2f} to guarantee locked profit even in sharp reversal.",
            "is_active_initial": False,
        },
        {
            "stage_num": 4,
            "phase": "Phase 4: Momentum Runner Trail",
            "trigger_condition": f"Option exceeds TP3 ${tp3_opt_px:.2f} (+150%+) / Stock ~${tp3_underlying:.2f}",
            "stop_level_option": round(tp2_opt_px, 2),
            "stop_level_stock": tp2_underlying,
            "stop_rule_label": "Trailing 8-EMA Daily Close",
            "risk_state": "House Money Convexity",
            "risk_badge": "bg-purple-500/20 text-purple-300 border-purple-500/30",
            "locked_profit": "Multi-Hundred % Asymmetric Payoff",
            "action": "Keep remaining 15-20% runners riding along the 8-day EMA on daily chart until a confirmed trend breakdown.",
            "is_active_initial": False,
        },
    ]

    # Phase 1: Defensive Adjustment & Rolling Playbook
    spread_strike = round(strike * 1.05 if is_call else strike * 0.95, 1)
    rolling_playbook = {
        "defensive_time_roll": {
            "title": "Roll Down & Out (21-DTE Defense)",
            "trigger_signal": f"Underlying consolidates near support and contract decays to 21 DTE (currently {dte} DTE).",
            "action": f"Close current {dte} DTE contract and roll expiration out 30–45 days. If underlying drifted, roll strike closer to current spot (${spot_price:.2f}).",
            "theta_relief": f"Resets theta clock (-${daily_theta_dollar:.2f}/day to ~40% slower decay) and grants position 30+ extra days to resolve.",
            "rule": "Never hold losing directional options past 21 DTE where gamma risk and theta slope accelerate into a cliff.",
        },
        "synthetic_spread_conversion": {
            "title": "Convert to Vertical Debit Spread (Theta Freeze)",
            "trigger_signal": "Stock enters multi-day sideways consolidation (-10% to -25% drawdown on option premium, but chart support holds).",
            "action": f"Sell higher OTM {'Call' if is_call else 'Put'} at ${spread_strike:.1f} strike against existing long contract to synthesize a debit spread.",
            "theta_relief": "Cuts net position theta burn by 60–80% and brings in upfront premium to lower your overall cost basis.",
            "rule": "Transforms an unhedged single-leg bleeding theta into a defined-risk spread with capped loss and reduced IV exposure.",
        },
        "profit_lock_roll": {
            "title": "Roll Up / Roll Out (Extract 100% Principal)",
            "trigger_signal": f"Option achieves TP2 (+100% at ${tp2_opt_px:.2f}).",
            "action": f"Sell the deep ITM/ATM contract at ${tp2_opt_px:.2f}. Take out 100% of your initial cash investment, and purchase a new OTM (~0.30Δ) contract with pure profits.",
            "theta_relief": "Extracts 100% of principal out of market risk. The new contract is a free roll ('house money') with zero risk to initial capital.",
            "rule": "Never let a 100% winner turn into a loss. Harvest principal and leverage market profits.",
        },
    }

    # Phase 1: Broker Bracket Order Generator (Standard, TOS, IBKR, Webull)
    half_contracts = (contracts // 2) if contracts > 0 else 0
    rem_contracts = (contracts - half_contracts) if contracts > 0 else 0
    opt_label = f"{contract_symbol}" if contract_symbol else f"{'CALL' if is_call else 'PUT'} ${strike:.1f}"

    broker_bracket_order = {
        "summary": f"GTC Advanced OCO Bracket Order for {contracts} contract(s)",
        "contracts_total": contracts,
        "entry_limit": entry_mid,
        "tp1_price": tp1_opt_px,
        "tp1_contracts": half_contracts,
        "tp2_price": tp2_opt_px,
        "tp2_contracts": rem_contracts,
        "stop_loss_price": sl_opt_px,
        "standard_text": (
            f"BUY TO OPEN {contracts} {opt_label} @ LIMIT ${entry_mid:.2f} GTC\n"
            f"[OCO BRACKET]:\n"
            f"  • SELL LIMIT {half_contracts} @ ${tp1_opt_px:.2f} (TP1 +50% Trim)\n"
            f"  • SELL LIMIT {rem_contracts} @ ${tp2_opt_px:.2f} (TP2 +100% Core Target)\n"
            f"  • STOP MARKET {contracts} @ ${sl_opt_px:.2f} (Hard Stop -50% Premium)"
        ),
        "tos_syntax": (
            f"BUY +{contracts} {opt_label} @{entry_mid:.2f} LMT GTC "
            f"OCO [SELL -{half_contracts} @{tp1_opt_px:.2f} LMT GTC / "
            f"SELL -{contracts} @{sl_opt_px:.2f} STP GTC]"
        ),
        "ibkr_syntax": (
            f"Action: BUY | Qty: {contracts} | Symbol: {opt_label} | Type: LMT | Lmt Price: {entry_mid:.2f} | TIF: GTC\n"
            f"Attach OCO Bracket:\n"
            f"  - Profit Taker LMT: ${tp1_opt_px:.2f} (Qty: {half_contracts})\n"
            f"  - Stop Loss STP: ${sl_opt_px:.2f} (Qty: {contracts})"
        ),
        "webull_syntax": (
            f"Order Type: Limit Buy @ ${entry_mid:.2f}\n"
            f"Take Profit Limit: ${tp1_opt_px:.2f} (Sell {half_contracts})\n"
            f"Stop Loss Stop: ${sl_opt_px:.2f} (Stop Market {contracts})"
        ),
    }

    return OptionTradePlan(
        entry_limit_price=entry_mid,
        entry_market_price=entry_ask,
        entry_zone=entry_zone,
        underlying_spot=round(spot_price, 2),
        underlying_invalidation_price=underlying_inval,
        tp1_option_price=tp1_opt_px,
        tp1_dollar_gain=tp1_gain,
        tp1_underlying_target=tp1_underlying,
        tp1_gain_pct=50.0,
        tp1_action=tp1_action,
        tp2_option_price=tp2_opt_px,
        tp2_dollar_gain=tp2_gain,
        tp2_underlying_target=tp2_underlying,
        tp2_gain_pct=100.0,
        tp2_action=tp2_action,
        tp3_runner_price=tp3_opt_px,
        tp3_dollar_gain=tp3_gain,
        tp3_underlying_target=tp3_underlying,
        tp3_gain_pct=150.0,
        tp3_action=tp3_action,
        stop_loss_option_price=sl_opt_px,
        stop_loss_dollar_loss=sl_dollar,
        total_planned_risk=planned_risk,
        max_capital_loss=max_capital,
        stop_loss_rule=stop_rule,
        daily_theta_decay=daily_theta_dollar,
        max_holding_period_days=max_hold_days,
        time_stop_rule=time_rule,
        probability_of_profit_pct=pop_pct,
        risk_reward_ratio=rr_ratio,
        expected_value_per_contract=ev_val,
        playbook_steps=playbook_steps,
        ratchet_ladder=ratchet_ladder,
        rolling_playbook=rolling_playbook,
        broker_bracket_order=broker_bracket_order,
    )


def compute_position_sizing(
    contract_cost: float,
    risk_cfg: RiskManagementConfig,
    custom_risk_pct: Optional[float] = None
) -> Tuple[int, float, float, float]:
    """Calculate position size and stop loss in dollars based on account equity and risk percentage.

    If 1 contract exceeds the risk budget, returns 0 contracts (does NOT force 1).
    """
    max_loss_one = contract_cost * 100.0
    effective_risk_pct = custom_risk_pct if custom_risk_pct is not None else risk_cfg.max_risk_pct
    budget = risk_cfg.account_equity * effective_risk_pct
    stop_loss_price = round(contract_cost * (1.0 - risk_cfg.stop_loss_pct), 2)

    if max_loss_one <= 0 or budget < max_loss_one:
        return 0, 0.0, stop_loss_price, 0.0

    contracts = int(budget // max_loss_one)
    total_max_loss = round(contracts * max_loss_one, 2)
    stop_loss_dollar = round(total_max_loss * risk_cfg.stop_loss_pct, 2)

    return contracts, total_max_loss, stop_loss_price, stop_loss_dollar


def rank_and_filter_contracts(
    df: pd.DataFrame,
    option_type: str,
    spot_price: float,
    filter_cfg: Optional[OptionsFilterConfig] = None,
    risk_cfg: Optional[RiskManagementConfig] = None
) -> Tuple[List[OptionSuggestion], Dict[str, int]]:
    """Filter by delta (0.30-0.55), volume, open interest, and spread; then rank candidates."""
    if df is None or df.empty or spot_price <= 0:
        return [], {"initial_count": 0}

    filter_cfg = filter_cfg or DEFAULT_CONFIG.options_filter
    risk_cfg = risk_cfg or DEFAULT_CONFIG.risk
    is_call = (option_type.upper() == "CALL")

    audit = {
        "initial_count": len(df),
        "rejected_min_bid": 0,
        "rejected_volume_oi": 0,
        "rejected_spread": 0,
        "rejected_delta": 0,
        "passed_strict": 0,
    }

    data = df.copy()

    # Pre-calculate Mid Price & Spread % of Mid
    data["mid_price"] = ((data["bid"] + data["ask"]) / 2.0).round(2)
    data["spread"] = (data["ask"] - data["bid"]).clip(lower=0.0).round(2)
    data["spread_pct_of_mid"] = data.apply(
        lambda r: (r["spread"] / r["mid_price"]) if r["mid_price"] > 0 else 1.0, axis=1
    )

    # Calculate Black-Scholes Greeks for every contract
    deltas = []
    gammas = []
    thetas = []
    vegas = []
    for _, row in data.iterrows():
        g = calculate_black_scholes_greeks(
            spot=spot_price,
            strike=float(row["strike"]),
            dte=int(row["dte"]),
            iv=float(row["impliedVolatility"]),
            is_call=is_call,
            risk_free_rate=filter_cfg.risk_free_rate
        )
        deltas.append(g.delta)
        gammas.append(g.gamma)
        thetas.append(g.theta)
        vegas.append(g.vega)
    data["delta"] = deltas
    data["abs_delta"] = [abs(d) for d in deltas]
    data["gamma"] = gammas
    data["theta"] = thetas
    data["vega"] = vegas

    if is_call:
        data["moneyness_pct"] = ((data["strike"] / spot_price - 1.0) * 100.0).round(2)
    else:
        data["moneyness_pct"] = ((spot_price / data["strike"] - 1.0) * 100.0).round(2)

    valid_rows = []
    for _, r in data.iterrows():
        if r["bid"] < filter_cfg.min_bid or r["ask"] <= r["bid"]:
            audit["rejected_min_bid"] += 1
            continue
        if r["volume"] < filter_cfg.min_volume or r["openInterest"] < filter_cfg.min_open_interest:
            audit["rejected_volume_oi"] += 1
            continue
        if r["spread_pct_of_mid"] > filter_cfg.max_spread_pct_of_mid:
            audit["rejected_spread"] += 1
            continue
        if not (filter_cfg.min_delta <= r["abs_delta"] <= filter_cfg.max_delta):
            audit["rejected_delta"] += 1
            continue
        valid_rows.append(r)

    audit["passed_strict"] = len(valid_rows)

    # Fallback if strict criteria yielded 0 candidates
    if not valid_rows:
        logger.info("Strict delta/liquidity filter yielded 0 contracts. Applying relaxed screening.")
        for _, r in data.iterrows():
            if r["bid"] < 0.02 or r["ask"] <= r["bid"]:
                continue
            if r["volume"] < 5 or r["openInterest"] < 25:
                continue
            if r["spread_pct_of_mid"] > 0.20:
                continue
            if not (0.20 <= r["abs_delta"] <= 0.65):
                continue
            valid_rows.append(r)

    if not valid_rows:
        return [], audit

    filtered = pd.DataFrame(valid_rows)

    if is_call:
        filtered["breakeven"] = (filtered["strike"] + filtered["ask"]).round(2)
        filtered["req_move"] = (((filtered["breakeven"] - spot_price) / spot_price) * 100.0).round(2)
    else:
        filtered["breakeven"] = (filtered["strike"] - filtered["ask"]).round(2)
        filtered["req_move"] = (((spot_price - filtered["breakeven"]) / spot_price) * 100.0).round(2)

    delta_diff = (filtered["abs_delta"] - filter_cfg.target_delta).abs()
    delta_score = (1.0 - (delta_diff / 0.15).clip(0.0, 1.0)) * 40.0
    spread_score = (1.0 - (filtered["spread_pct_of_mid"] / filter_cfg.max_spread_pct_of_mid).clip(0.0, 1.0)) * 35.0
    log_liq = np.log1p(filtered["volume"] + filtered["openInterest"])
    liq_score = (log_liq / 9.5).clip(0.0, 1.0) * 25.0

    filtered["rank_score"] = (delta_score + spread_score + liq_score).round(1)
    ranked = filtered.sort_values(by="rank_score", ascending=False).head(filter_cfg.top_n_suggestions)

    suggestions: List[OptionSuggestion] = []
    for _, row in ranked.iterrows():
        dte = int(row["dte"])
        iv_pct = round(float(row["impliedVolatility"]) * 100.0, 1)
        ask_val = float(row["ask"])
        bid_val = float(row["bid"])
        mid_val = float(row["mid_price"])
        spread_pct = round(float(row["spread_pct_of_mid"]) * 100.0, 1)

        contracts, total_loss, stop_px, stop_dollar = compute_position_sizing(ask_val, risk_cfg)

        warnings = []
        if contracts == 0:
            budget_val = risk_cfg.account_equity * (risk_cfg.max_risk_pct)
            warnings.append(
                f"Capital requirement (${ask_val * 100:.0f}/contract) exceeds risk allocation budget (${budget_val:.0f}). Sized to 0 contracts."
            )
        if iv_pct >= filter_cfg.elevated_iv_threshold:
            warnings.append(f"Elevated IV ({iv_pct}%) – High volatility premium; consider debit spread.")
        if spread_pct > 7.0:
            warnings.append(f"Spread warning ({spread_pct}% of mid) – Use limit orders.")
        if int(row["openInterest"]) < 300:
            warnings.append(f"Moderate OI ({int(row['openInterest']):,}) – Monitor liquidity.")
        if dte < 21:
            warnings.append(f"Theta acceleration: {dte} DTE remaining.")

        t_plan = build_option_trade_plan(
            spot_price=spot_price,
            strike=float(row["strike"]),
            bid=bid_val,
            ask=ask_val,
            mid_price=mid_val,
            delta=float(row["delta"]),
            gamma=float(row.get("gamma", 0.0)),
            theta=float(row.get("theta", 0.0)),
            dte=dte,
            iv_pct=iv_pct,
            is_call=is_call,
            contracts=contracts,
            total_dollar_risk=total_loss,
            stop_loss_px=stop_px,
            stop_loss_dollar=stop_dollar,
            breakeven_px=float(row["breakeven"]),
            contract_symbol=str(row["contractSymbol"]),
        )

        suggestions.append(
            OptionSuggestion(
                contract_symbol=str(row["contractSymbol"]),
                option_type=option_type,
                strike=float(row["strike"]),
                expiration=str(row["expiration"]),
                dte=dte,
                spot_price=round(spot_price, 2),
                bid=bid_val,
                ask=ask_val,
                mid_price=mid_val,
                spread=round(float(row["spread"]), 2),
                spread_pct_of_mid=spread_pct,
                volume=int(row["volume"]),
                open_interest=int(row["openInterest"]),
                implied_volatility_pct=iv_pct,
                delta=float(row["delta"]),
                gamma=float(row.get("gamma", 0.0)),
                theta=float(row.get("theta", 0.0)),
                vega=float(row.get("vega", 0.0)),
                moneyness_pct=float(row["moneyness_pct"]),
                in_the_money=bool(row.get("inTheMoney", False)),
                breakeven_price=float(row["breakeven"]),
                required_move_pct=float(row["req_move"]),
                rank_score=float(row["rank_score"]),
                max_loss_per_contract=round(ask_val * 100.0, 2),
                suggested_contracts=contracts,
                total_dollar_risk=total_loss,
                suggested_stop_loss_price=stop_px,
                stop_loss_dollar_risk=stop_dollar,
                risk_warnings=warnings,
                trade_plan=t_plan,
            )
        )

    return suggestions, audit


def build_debit_spread(
    primary_opt: OptionSuggestion,
    chain_df: pd.DataFrame,
    spot_price: float,
    risk_cfg: RiskManagementConfig
) -> Optional[DebitSpreadSuggestion]:
    """Construct a defined-risk vertical debit spread pairing with the primary contract."""
    if chain_df is None or chain_df.empty:
        return None

    is_call = (primary_opt.option_type == "CALL")
    same_exp = chain_df[chain_df["expiration"] == primary_opt.expiration].copy()
    if same_exp.empty:
        return None

    if is_call:
        partner_candidates = same_exp[
            (same_exp["strike"] > primary_opt.strike) &
            (same_exp["bid"] > 0.05)
        ].sort_values(by="strike", ascending=True)
    else:
        partner_candidates = same_exp[
            (same_exp["strike"] < primary_opt.strike) &
            (same_exp["bid"] > 0.05)
        ].sort_values(by="strike", ascending=False)

    if partner_candidates.empty:
        return None

    partner = partner_candidates.iloc[0]
    short_strike = float(partner["strike"])
    short_bid = float(partner["bid"])
    width = abs(short_strike - primary_opt.strike)

    net_debit = round(primary_opt.ask - short_bid, 2)
    if net_debit <= 0.10 or net_debit >= width:
        return None

    max_loss = round(net_debit * 100.0, 2)
    max_profit = round((width - net_debit) * 100.0, 2)
    rr_ratio = round(max_profit / max_loss, 2) if max_loss > 0 else 0.0

    if is_call:
        be_price = round(primary_opt.strike + net_debit, 2)
        spread_type = "Bull Call Debit Spread"
    else:
        be_price = round(primary_opt.strike - net_debit, 2)
        spread_type = "Bear Put Debit Spread"

    contracts, total_loss, _, _ = compute_position_sizing(net_debit, risk_cfg)

    short_delta = calculate_black_scholes_delta(
        spot_price, short_strike, primary_opt.dte,
        float(partner.get("impliedVolatility", 0.30)), is_call
    )

    notes = (
        f"Caps max loss to ${max_loss:.2f} while slashing net IV exposure. "
        f"Breakeven at ${be_price:.2f} (Max profit ${max_profit:.2f}/contract)."
    )

    spread_plan = {
        "entry_strategy": f"Limit order at net debit ${net_debit:.2f} (avoid paying wide bid/ask).",
        "target_profit_pct": 75.0,
        "target_spread_value": round(net_debit + (width - net_debit) * 0.75, 2),
        "target_dollar_gain": round(max_profit * 0.75, 2),
        "stop_loss_value": round(net_debit * 0.50, 2),
        "stop_dollar_loss": round(max_loss * 0.50, 2),
        "max_holding_period_days": min(14, max(4, primary_opt.dte - 5)),
        "time_stop_rule": "Close spread 3–5 trading days prior to expiration if underlying has not crossed short strike.",
        "playbook_steps": [
            f"1. Entry: Execute as single-order vertical debit spread at net debit limit ${net_debit:.2f}.",
            f"2. Profit Target: Set GTC limit order to close at ${net_debit + (width - net_debit) * 0.75:.2f} (75% of max profit).",
            f"3. Risk Control: Close spread if net value drops to ${net_debit * 0.50:.2f} (-50% loss).",
            f"4. Early Exit: Never hold into expiration Friday; close at least 3-5 days before expiration to eliminate pin risk."
        ]
    }

    return DebitSpreadSuggestion(
        spread_type=spread_type,
        expiration=primary_opt.expiration,
        dte=primary_opt.dte,
        long_contract=primary_opt.contract_symbol,
        long_strike=primary_opt.strike,
        long_ask=primary_opt.ask,
        long_delta=primary_opt.delta,
        short_contract=str(partner["contractSymbol"]),
        short_strike=short_strike,
        short_bid=short_bid,
        short_delta=short_delta,
        net_debit=net_debit,
        max_loss_per_contract=max_loss,
        max_profit_per_contract=max_profit,
        breakeven_price=be_price,
        risk_reward_ratio=rr_ratio,
        suggested_contracts=contracts,
        total_dollar_risk=total_loss,
        spread_notes=notes,
        trade_plan=spread_plan,
    )


def build_high_risk_setup(
    chain_df: pd.DataFrame,
    option_type: str,
    spot_price: float,
    high_risk_cfg: HighRiskOptionsFilterConfig,
    risk_cfg: RiskManagementConfig
) -> Optional[HighRiskTradeSetup]:
    """Construct an asymmetric high-risk trade setup: OTM moonshot contract (0.15-0.28Delta) + high R:R lotto spread."""
    if chain_df is None or chain_df.empty or spot_price <= 0:
        return None

    is_call = (option_type.upper() == "CALL")
    data = chain_df.copy()

    # Filter by bid, spread and reasonable liquidity
    data["mid_price"] = ((data["bid"] + data["ask"]) / 2.0).round(2)
    data["spread"] = (data["ask"] - data["bid"]).clip(lower=0.0).round(2)
    data["spread_pct"] = data.apply(
        lambda r: (r["spread"] / r["mid_price"]) if r["mid_price"] > 0 else 1.0, axis=1
    )

    deltas = []
    for _, row in data.iterrows():
        d = calculate_black_scholes_delta(
            spot=spot_price,
            strike=float(row["strike"]),
            dte=int(row["dte"]),
            iv=float(row.get("impliedVolatility", 0.40)),
            is_call=is_call,
            risk_free_rate=0.045
        )
        deltas.append(d)
    data["delta"] = deltas
    data["abs_delta"] = [abs(d) for d in deltas]

    # Look for OTM contracts in 0.15 - 0.28 delta range with DTE >= min_dte
    candidates = data[
        (data["bid"] >= 0.05) &
        (data["ask"] > data["bid"]) &
        (data["dte"] >= high_risk_cfg.min_dte) &
        (data["dte"] <= 45) &
        (data["abs_delta"] >= high_risk_cfg.min_delta) &
        (data["abs_delta"] <= high_risk_cfg.max_delta) &
        (data["spread_pct"] <= high_risk_cfg.max_spread_pct_of_mid)
    ].copy()

    if candidates.empty:
        # Relax slightly if no candidates in strict range
        candidates = data[
            (data["bid"] >= 0.05) &
            (data["ask"] > data["bid"]) &
            (data["abs_delta"] >= 0.12) &
            (data["abs_delta"] <= 0.32)
        ].copy()

    if candidates.empty:
        return None

    # Pick contract closest to target delta (0.22)
    candidates["delta_dist"] = (candidates["abs_delta"] - high_risk_cfg.target_delta).abs()
    best_row = candidates.sort_values(by=["delta_dist", "ask"], ascending=[True, True]).iloc[0]

    strike = float(best_row["strike"])
    ask_val = float(best_row["ask"])
    mid_val = float(best_row["mid_price"])
    dte = int(best_row["dte"])
    delta_val = float(best_row["delta"])
    exp = str(best_row["expiration"])

    if is_call:
        be_price = round(strike + ask_val, 2)
        req_move = round(((be_price - spot_price) / spot_price) * 100.0, 2)
        moneyness = round(((strike / spot_price) - 1.0) * 100.0, 1)
        sim_price = spot_price * 1.10
        intrinsic = max(0.0, sim_price - strike)
        leverage = round((intrinsic / ask_val), 1) if ask_val > 0 else 2.5
    else:
        be_price = round(strike - ask_val, 2)
        req_move = round(((spot_price - be_price) / spot_price) * 100.0, 2)
        moneyness = round(((spot_price / strike) - 1.0) * 100.0, 1)
        sim_price = spot_price * 0.90
        intrinsic = max(0.0, strike - sim_price)
        leverage = round((intrinsic / ask_val), 1) if ask_val > 0 else 2.5

    # Position size with trade risk budget (uncapped)
    contracts, total_loss, _, _ = compute_position_sizing(
        ask_val, risk_cfg, custom_risk_pct=high_risk_cfg.speculative_risk_pct
    )

    # Attempt to build asymmetric lotto spread (target >= 2.5:1 R:R)
    same_exp = data[data["expiration"] == exp]
    lotto_spread = None
    if is_call:
        short_partners = same_exp[
            (same_exp["strike"] > strike) &
            (same_exp["bid"] > 0.05) &
            (same_exp["abs_delta"] < abs(delta_val))
        ].sort_values(by="strike", ascending=True)
    else:
        short_partners = same_exp[
            (same_exp["strike"] < strike) &
            (same_exp["bid"] > 0.05) &
            (same_exp["abs_delta"] < abs(delta_val))
        ].sort_values(by="strike", ascending=False)

    if not short_partners.empty:
        partner = short_partners.iloc[0]
        s_strike = float(partner["strike"])
        s_bid = float(partner["bid"])
        w = abs(s_strike - strike)
        net_d = round(ask_val - s_bid, 2)
        if 0.10 < net_d < w:
            m_loss = round(net_d * 100.0, 2)
            m_prof = round((w - net_d) * 100.0, 2)
            rr = round(m_prof / m_loss, 2) if m_loss > 0 else 0.0
            if rr >= 2.0:
                lotto_be = round(strike + net_d, 2) if is_call else round(strike - net_d, 2)
                lotto_contracts, lotto_total_loss, _, _ = compute_position_sizing(
                    net_d, risk_cfg, custom_risk_pct=high_risk_cfg.speculative_risk_pct
                )
                lotto_spread = DebitSpreadSuggestion(
                    spread_type=f"Asymmetric {option_type.capitalize()} Lotto Spread ({rr:.1f}:1 R:R)",
                    expiration=exp,
                    dte=dte,
                    long_contract=str(best_row["contractSymbol"]),
                    long_strike=strike,
                    long_ask=ask_val,
                    long_delta=delta_val,
                    short_contract=str(partner["contractSymbol"]),
                    short_strike=s_strike,
                    short_bid=s_bid,
                    short_delta=float(partner.get("delta", 0.10)),
                    net_debit=net_d,
                    max_loss_per_contract=m_loss,
                    max_profit_per_contract=m_prof,
                    breakeven_price=lotto_be,
                    risk_reward_ratio=rr,
                    suggested_contracts=lotto_contracts,
                    total_dollar_risk=lotto_total_loss,
                    spread_notes=f"High-asymmetry spread targeting {rr:.1f}:1 payout. Max profit ${m_prof:.0f} on ${m_loss:.0f} risk.",
                )

    high_risk_plan = {
        "entry_strategy": f"Limit order at mid-price ${mid_val:.2f} (ask is ${ask_val:.2f}).",
        "tp1": {
            "gain_pct": 100.0,
            "option_price": round(ask_val * 2.0, 2),
            "dollar_gain": round(ask_val * 100.0, 2),
            "action": "Sell 50% of contracts at +100% gain (2x). This recoups 100% of initial risk capital — position becomes a FREE RIDE (House Money)!",
        },
        "tp2": {
            "gain_pct": 250.0,
            "option_price": round(ask_val * 3.5, 2),
            "dollar_gain": round(ask_val * 250.0, 2),
            "action": "Take profit on next 25–35% of contracts at +250% gain (3.5x).",
        },
        "tp3_moonshot": {
            "gain_pct": 500.0,
            "option_price": round(ask_val * 6.0, 2),
            "dollar_gain": round(ask_val * 500.0, 2),
            "action": "Hold remaining lotto runners for parabolic gamma surge.",
        },
        "stop_loss": {
            "option_price": round(ask_val * 0.50, 2),
            "dollar_loss": round(ask_val * 50.0, 2),
            "action": f"Hard stop at ${ask_val * 0.50:.2f} (-50% premium loss).",
        },
        "time_stop": {
            "max_holding_days": 5,
            "rule": "Close position if momentum does not follow through within 5 trading days. OTM options decay rapidly.",
        },
        "pop_pct": calculate_probability_of_profit(spot_price, be_price, dte, float(best_row.get("impliedVolatility", 0.40)), is_call),
        "playbook_steps": [
            f"1. Entry: Place limit order at mid-price ${mid_val:.2f}.",
            f"2. Free Ride Scale (TP1): At ${ask_val * 2.0:.2f} (+100%), sell 50% of contracts to recoup your full initial capital.",
            f"3. Core Target (TP2): At ${ask_val * 3.5:.2f} (+250%), sell another 25-35% of contracts.",
            f"4. Moonshot Runner: Leave 15-25% runners for 5x-10x gamma payoff.",
            f"5. Time Stop: Close trade after 5 trading days if no strong price impulse occurs."
        ]
    }

    warnings = [
        f"⚡ High Risk (OTM {abs(moneyness)}%): Low probability of expiring ITM (~20-25%).",
        f"⚡ Rapid Theta Decay: {dte} DTE remaining.",
        "⚡ Speculative Capital Only: Uncapped sizing utilizing full trade risk budget.",
    ]

    setup_title = f"Asymmetric Moonshot {option_type.capitalize()} ({delta_val:+.2f}Delta)"

    return HighRiskTradeSetup(
        setup_name=setup_title,
        contract_symbol=str(best_row["contractSymbol"]),
        option_type=option_type,
        strike=strike,
        expiration=exp,
        dte=dte,
        bid=float(best_row["bid"]),
        ask=ask_val,
        delta=delta_val,
        moneyness_pct=moneyness,
        breakeven_price=be_price,
        required_move_pct=req_move,
        upside_leverage=max(leverage, 2.0),
        suggested_contracts=contracts,
        total_dollar_risk=total_loss,
        lotto_spread=lotto_spread,
        risk_warnings=warnings,
        trade_plan=high_risk_plan,
    )


def build_zero_dte_setup(
    chain_df: pd.DataFrame,
    option_type: str,
    spot_price: float,
    zero_dte_cfg: ZeroDteOptionsFilterConfig,
    risk_cfg: RiskManagementConfig,
    symbol: str = "",
    bias_str: str = "BULLISH",
) -> Optional[ZeroDteTradeSetup]:
    """Construct dual 0DTE setups: (1) ATM Momentum Scalp + (2) OTM Gamma Lotto + Defined-Risk Spread."""
    if chain_df is None or chain_df.empty or spot_price <= 0:
        return None

    is_call = (option_type.upper() == "CALL")
    data = chain_df.copy()

    # Determine earliest available expiration in front cycle (0DTE or next closest)
    min_dte_val = int(data["dte"].min())
    target_exp = str(data[data["dte"] == min_dte_val]["expiration"].iloc[0])
    cycle_df = data[data["expiration"] == target_exp].copy()
    if cycle_df.empty:
        return None

    # Compute mid, spread, and Black-Scholes Greeks for every strike
    cycle_df["mid_price"] = ((cycle_df["bid"] + cycle_df["ask"]) / 2.0).round(2)
    cycle_df["spread"] = (cycle_df["ask"] - cycle_df["bid"]).clip(lower=0.0).round(2)
    cycle_df["spread_pct"] = cycle_df.apply(
        lambda r: (r["spread"] / r["mid_price"]) if r["mid_price"] > 0 else 1.0, axis=1
    )

    deltas, gammas, thetas = [], [], []
    for _, row in cycle_df.iterrows():
        g = calculate_black_scholes_greeks(
            spot=spot_price,
            strike=float(row["strike"]),
            dte=min_dte_val,
            iv=float(row.get("impliedVolatility", 0.25)),
            is_call=is_call,
            risk_free_rate=zero_dte_cfg.risk_free_rate
        )
        deltas.append(g.delta)
        gammas.append(g.gamma)
        thetas.append(g.theta)

    cycle_df["delta"] = deltas
    cycle_df["gamma"] = gammas
    cycle_df["theta"] = thetas
    cycle_df["abs_delta"] = [abs(d) for d in deltas]

    # Valid tradable contracts
    valid = cycle_df[
        (cycle_df["bid"] >= zero_dte_cfg.min_bid) &
        (cycle_df["ask"] > cycle_df["bid"])
    ].copy()

    if valid.empty:
        return None

    # 1. SCALP SETUP (Target ATM ~0.50 Delta, min spread)
    scalp_cands = valid[
        (valid["abs_delta"] >= zero_dte_cfg.min_scalp_delta) &
        (valid["abs_delta"] <= zero_dte_cfg.max_scalp_delta)
    ].copy()
    if scalp_cands.empty:
        scalp_cands = valid.copy()

    scalp_cands["scalp_dist"] = (scalp_cands["abs_delta"] - zero_dte_cfg.target_scalp_delta).abs()
    scalp_row = scalp_cands.sort_values(by=["scalp_dist", "spread_pct"], ascending=[True, True]).iloc[0]

    s_strike = float(scalp_row["strike"])
    s_ask = float(scalp_row["ask"])
    s_bid = float(scalp_row["bid"])
    s_mid = float(scalp_row["mid_price"])
    s_delta = float(scalp_row["delta"])
    s_gamma = float(scalp_row["gamma"])
    s_theta = float(scalp_row["theta"])
    s_theta_hr = round(s_theta / 6.5, 3)

    if is_call:
        s_be = round(s_strike + s_ask, 2)
        s_req_move = round(((s_be - spot_price) / spot_price) * 100.0, 2)
    else:
        s_be = round(s_strike - s_ask, 2)
        s_req_move = round(((spot_price - s_be) / spot_price) * 100.0, 2)

    s_contracts, s_risk, _, _ = compute_position_sizing(
        s_ask, risk_cfg, custom_risk_pct=zero_dte_cfg.speculative_risk_pct
    )

    # 2. LOTTO MOONSHOT SETUP (Target OTM ~0.20 Delta, extreme gamma convexity)
    lotto_cands = valid[
        (valid["abs_delta"] >= zero_dte_cfg.min_lotto_delta) &
        (valid["abs_delta"] <= zero_dte_cfg.max_lotto_delta)
    ].copy()
    if lotto_cands.empty:
        if is_call:
            lotto_cands = valid[valid["strike"] > spot_price].copy()
        else:
            lotto_cands = valid[valid["strike"] < spot_price].copy()
        if lotto_cands.empty:
            lotto_cands = valid.copy()

    lotto_cands["lotto_dist"] = (lotto_cands["abs_delta"] - zero_dte_cfg.target_lotto_delta).abs()
    lotto_row = lotto_cands.sort_values(by=["lotto_dist", "ask"], ascending=[True, True]).iloc[0]

    l_strike = float(lotto_row["strike"])
    l_ask = float(lotto_row["ask"])
    l_bid = float(lotto_row["bid"])
    l_delta = float(lotto_row["delta"])
    l_gamma = float(lotto_row["gamma"])

    if is_call:
        l_be = round(l_strike + l_ask, 2)
        l_req_move = round(((l_be - spot_price) / spot_price) * 100.0, 2)
        sim_px = spot_price * 1.015  # 1.5% intraday rally
        intrinsic = max(0.0, sim_px - l_strike)
    else:
        l_be = round(l_strike - l_ask, 2)
        l_req_move = round(((spot_price - l_be) / spot_price) * 100.0, 2)
        sim_px = spot_price * 0.985  # 1.5% intraday drop
        intrinsic = max(0.0, l_strike - sim_px)

    upside_lev = round(intrinsic / l_ask, 1) if l_ask > 0 else 3.0
    upside_lev = max(upside_lev, 2.5)

    l_contracts, l_risk, _, _ = compute_position_sizing(
        l_ask, risk_cfg, custom_risk_pct=zero_dte_cfg.speculative_risk_pct
    )

    # 3. ASYMMETRIC 0DTE LOTTO SPREAD
    lotto_spread = None
    if is_call:
        short_partners = valid[
            (valid["strike"] > l_strike) &
            (valid["bid"] >= 0.02)
        ].sort_values(by="strike", ascending=True)
    else:
        short_partners = valid[
            (valid["strike"] < l_strike) &
            (valid["bid"] >= 0.02)
        ].sort_values(by="strike", ascending=False)

    best_partner = None
    best_rr = 0.0
    best_net_d = 0.0
    best_width = 0.0

    for _, p_row in short_partners.head(6).iterrows():
        p_strike = float(p_row["strike"])
        p_bid = float(p_row["bid"])
        width = abs(p_strike - l_strike)
        net_d = round(l_ask - p_bid, 2)
        if 0.05 < net_d < width:
            m_loss = round(net_d * 100.0, 2)
            m_prof = round((width - net_d) * 100.0, 2)
            rr = round(m_prof / m_loss, 2) if m_loss > 0 else 0.0
            if rr >= 2.0 and rr > best_rr:
                best_rr = rr
                best_partner = p_row
                best_net_d = net_d
                best_width = width

    if best_partner is not None:
        p_strike = float(best_partner["strike"])
        p_bid = float(best_partner["bid"])
        m_loss = round(best_net_d * 100.0, 2)
        m_prof = round((best_width - best_net_d) * 100.0, 2)
        sp_be = round(l_strike + best_net_d, 2) if is_call else round(l_strike - best_net_d, 2)
        sp_contracts, sp_loss, _, _ = compute_position_sizing(
            best_net_d, risk_cfg, custom_risk_pct=zero_dte_cfg.speculative_risk_pct
        )
        lotto_spread = DebitSpreadSuggestion(
            spread_type=f"0DTE Asymmetric {option_type.capitalize()} Spread ({best_rr:.1f}:1 R:R)",
            expiration=target_exp,
            dte=min_dte_val,
            long_contract=str(lotto_row["contractSymbol"]),
            long_strike=l_strike,
            long_ask=l_ask,
            long_delta=l_delta,
            short_contract=str(best_partner["contractSymbol"]),
            short_strike=p_strike,
            short_bid=p_bid,
            short_delta=float(best_partner.get("delta", 0.08)),
            net_debit=best_net_d,
            max_loss_per_contract=m_loss,
            max_profit_per_contract=m_prof,
            breakeven_price=sp_be,
            risk_reward_ratio=best_rr,
            suggested_contracts=sp_contracts,
            total_dollar_risk=sp_loss,
            spread_notes=f"0DTE defined-risk spread targeting {best_rr:.1f}:1 payout. Max profit ${m_prof:.0f} on ${m_loss:.0f} risk.",
        )

    velocity_hr = round(abs(s_req_move) / 6.5, 2)

    zero_dte_plan = {
        "entry_strategy": f"Limit order at mid-price ${s_mid:.2f} on intraday momentum confirmation.",
        "tp1_scalp": {
            "gain_pct": 30.0,
            "option_price": round(s_ask * 1.30, 2),
            "action": "Sell 50–70% of contracts on quick +30% momentum surge (15–30 min execution window).",
        },
        "tp2_runner": {
            "gain_pct": 75.0,
            "option_price": round(s_ask * 1.75, 2),
            "action": "Exit remaining contracts at +75% or when 5-min candle breaks under 9 EMA.",
        },
        "stop_loss": {
            "option_price": round(s_ask * 0.65, 2),
            "gain_pct": -35.0,
            "action": f"Strict intraday cut at ${s_ask * 0.65:.2f} (-35% stop). Never hold losing 0DTE contracts.",
        },
        "intraday_time_stop": {
            "max_minutes": 60,
            "rule": f"Exit if underlying fails to break out within 45–60 minutes. Current theta decay is -${abs(s_theta_hr * 100.0):.1f}/hour!",
        },
        "playbook_steps": [
            f"1. Entry: Limit order at mid-price ${s_mid:.2f}.",
            f"2. Quick Scalp (TP1): Sell 50-70% at +30% (${s_ask * 1.30:.2f}) within 15-30 minutes.",
            f"3. Momentum Runner (TP2): Exit balance at +75% (${s_ask * 1.75:.2f}) or 9-EMA trail.",
            f"4. Hard Stop: Cut immediately if option drops 35% (${s_ask * 0.65:.2f}). No hoping.",
            f"5. 60-Minute Rule: If trade hasn't moved in 1 hour, exit flat to avoid severe intraday theta burn."
        ]
    }

    warnings = [
        f"⚡ 0DTE Intraday Alert: Expires {target_exp} (DTE: {min_dte_val}). High velocity intraday action.",
        f"⚡ Theta Burn Rate: -${abs(s_theta_hr * 100.0):.1f}/hour per contract. Trade moves must occur rapidly.",
        "⚡ Uncapped Trade Risk: Contracts sized strictly to your full trade risk budget.",
    ]

    return ZeroDteTradeSetup(
        symbol=symbol or "UNKNOWN",
        spot_price=spot_price,
        bias=bias_str,
        expiration=target_exp,
        dte=min_dte_val,
        scalp_contract=str(scalp_row["contractSymbol"]),
        scalp_strike=s_strike,
        scalp_type=option_type,
        scalp_bid=s_bid,
        scalp_ask=s_ask,
        scalp_delta=s_delta,
        scalp_gamma=s_gamma,
        scalp_theta=s_theta,
        scalp_theta_per_hour=s_theta_hr,
        scalp_suggested_contracts=s_contracts,
        scalp_total_risk=s_risk,
        scalp_breakeven=s_be,
        scalp_req_move_pct=s_req_move,
        lotto_contract=str(lotto_row["contractSymbol"]),
        lotto_strike=l_strike,
        lotto_bid=l_bid,
        lotto_ask=l_ask,
        lotto_delta=l_delta,
        lotto_gamma=l_gamma,
        lotto_upside_leverage=upside_lev,
        lotto_suggested_contracts=l_contracts,
        lotto_total_risk=l_risk,
        lotto_breakeven=l_be,
        lotto_req_move_pct=l_req_move,
        lotto_spread=lotto_spread,
        breakeven_velocity_per_hour=velocity_hr,
        risk_warnings=warnings,
        trade_plan=zero_dte_plan,
    )


def suggest_options(
    signal: TradeSignal,
    spot_price: float,
    calls_df: pd.DataFrame,
    puts_df: pd.DataFrame,
    filter_cfg: Optional[OptionsFilterConfig] = None,
    risk_cfg: Optional[RiskManagementConfig] = None,
    high_risk_cfg: Optional[HighRiskOptionsFilterConfig] = None,
) -> ScreeningResult:
    """Generate filtered options suggestions with Delta targeting, debit spreads, and high-risk setups."""
    filter_cfg = filter_cfg or DEFAULT_CONFIG.options_filter
    risk_cfg = risk_cfg or DEFAULT_CONFIG.risk
    high_risk_cfg = high_risk_cfg or DEFAULT_CONFIG.high_risk_filter

    if signal.bias == BiasDirection.NEUTRAL or signal.is_earnings_blackout:
        return ScreeningResult()

    if signal.bias == BiasDirection.BULLISH:
        suggestions, audit = rank_and_filter_contracts(calls_df, "CALL", spot_price, filter_cfg, risk_cfg)
        chain_for_spreads = calls_df
        opt_type = "CALL"
    else:
        suggestions, audit = rank_and_filter_contracts(puts_df, "PUT", spot_price, filter_cfg, risk_cfg)
        chain_for_spreads = puts_df
        opt_type = "PUT"

    # Always generate High-Risk / Asymmetric trade setup if directional bias exists
    high_risk_setup = build_high_risk_setup(
        chain_for_spreads, opt_type, spot_price, high_risk_cfg, risk_cfg
    )

    if not suggestions:
        return ScreeningResult(
            high_risk_setup=high_risk_setup,
            audit_log=audit
        )

    avg_iv = np.mean([s.implied_volatility_pct for s in suggestions])
    elevated_iv = (avg_iv >= filter_cfg.elevated_iv_threshold)

    spread_recs: List[DebitSpreadSuggestion] = []
    top_spread = build_debit_spread(suggestions[0], chain_for_spreads, spot_price, risk_cfg)
    if top_spread:
        spread_recs.append(top_spread)

    return ScreeningResult(
        single_leg_suggestions=suggestions,
        spread_suggestions=spread_recs,
        high_risk_setup=high_risk_setup,
        elevated_iv=elevated_iv,
        avg_iv_pct=round(avg_iv, 1),
        audit_log=audit,
    )


def calculate_chain_analytics(
    spot: float,
    dte: int,
    calls_df: pd.DataFrame,
    puts_df: pd.DataFrame
) -> Dict[str, Any]:
    """Calculate Max Pain, Expected Move, Put-Call Ratios, and Open Interest breakdown."""
    if spot <= 0:
        all_s = []
        if calls_df is not None and not calls_df.empty and "strike" in calls_df.columns:
            all_s.extend(calls_df["strike"].dropna().tolist())
        if puts_df is not None and not puts_df.empty and "strike" in puts_df.columns:
            all_s.extend(puts_df["strike"].dropna().tolist())
        if all_s:
            import pandas as pd
            spot = float(pd.Series(all_s).median())

    if calls_df is None or puts_df is None or calls_df.empty or puts_df.empty:
        return {
            "expected_move": 0.0,
            "expected_move_pct": 0.0,
            "expected_range_low": spot,
            "expected_range_high": spot,
            "expected_lower": spot,
            "expected_upper": spot,
            "max_pain": spot,
            "atm_strike": spot,
            "pcr_volume": 1.0,
            "pcr_oi": 1.0,
            "pcr_bias": "Neutral / Balanced",
            "pcr_sentiment": "Neutral / Balanced",
            "total_call_volume": 0,
            "total_put_volume": 0,
            "total_call_oi": 0,
            "total_put_oi": 0,
        }

    total_call_vol = int(calls_df["volume"].fillna(0).sum())
    total_put_vol = int(puts_df["volume"].fillna(0).sum())
    total_call_oi = int(calls_df["openInterest"].fillna(0).sum())
    total_put_oi = int(puts_df["openInterest"].fillna(0).sum())

    pcr_volume = round(total_put_vol / total_call_vol, 2) if total_call_vol > 0 else 1.0
    pcr_oi = round(total_put_oi / total_call_oi, 2) if total_call_oi > 0 else 1.0

    if pcr_volume < 0.70:
        pcr_bias = "Bullish (Call Heavy)"
    elif pcr_volume > 1.15:
        pcr_bias = "Bearish / Hedging (Put Heavy)"
    else:
        pcr_bias = "Neutral / Balanced"

    all_strikes = sorted(list(set(calls_df["strike"].dropna()).union(set(puts_df["strike"].dropna()))))

    # 1. Max Pain calculation
    loss_by_strike: Dict[float, float] = {}
    for test_strike in all_strikes:
        call_loss = 0.0
        for _, r in calls_df.iterrows():
            k = float(r["strike"])
            oi = float(r.get("openInterest", 0) or 0)
            if test_strike > k:
                call_loss += (test_strike - k) * oi * 100.0

        put_loss = 0.0
        for _, r in puts_df.iterrows():
            k = float(r["strike"])
            oi = float(r.get("openInterest", 0) or 0)
            if test_strike < k:
                put_loss += (k - test_strike) * oi * 100.0

        loss_by_strike[test_strike] = call_loss + put_loss

    max_pain = min(loss_by_strike, key=loss_by_strike.get) if loss_by_strike else spot

    # 2. Expected Move calculation
    atm_strike = min(all_strikes, key=lambda s: abs(s - spot)) if all_strikes else spot
    c_match = calls_df[calls_df["strike"] == atm_strike]
    p_match = puts_df[puts_df["strike"] == atm_strike]

    c_price = 0.0
    if not c_match.empty:
        ask = float(c_match["ask"].iloc[0] or 0)
        bid = float(c_match["bid"].iloc[0] or 0)
        c_price = (ask + bid) / 2.0 if (ask + bid) > 0 else float(c_match["lastPrice"].iloc[0] or 0)

    p_price = 0.0
    if not p_match.empty:
        ask = float(p_match["ask"].iloc[0] or 0)
        bid = float(p_match["bid"].iloc[0] or 0)
        p_price = (ask + bid) / 2.0 if (ask + bid) > 0 else float(p_match["lastPrice"].iloc[0] or 0)

    straddle_price = c_price + p_price
    if straddle_price > 0:
        expected_move = round(straddle_price * 0.85, 2)
    else:
        atm_iv = 0.40
        if not c_match.empty and float(c_match["impliedVolatility"].iloc[0] or 0) > 0:
            atm_iv = float(c_match["impliedVolatility"].iloc[0])
        expected_move = round(spot * atm_iv * math.sqrt(max(dte, 0.5) / 365.0), 2)

    expected_move_pct = round((expected_move / spot) * 100.0, 2) if spot > 0 else 0.0
    expected_range_low = round(spot - expected_move, 2)
    expected_range_high = round(spot + expected_move, 2)

    return {
        "expected_move": expected_move,
        "expected_move_pct": expected_move_pct,
        "expected_range_low": expected_range_low,
        "expected_range_high": expected_range_high,
        "expected_lower": expected_range_low,
        "expected_upper": expected_range_high,
        "max_pain": round(max_pain, 2),
        "atm_strike": round(atm_strike, 2),
        "pcr_volume": pcr_volume,
        "pcr_oi": pcr_oi,
        "pcr_bias": pcr_bias,
        "pcr_sentiment": pcr_bias,
        "total_call_volume": total_call_vol,
        "total_put_volume": total_put_vol,
        "total_call_oi": total_call_oi,
        "total_put_oi": total_put_oi,
    }


def build_chain_matrix(
    spot: float,
    calls_df: pd.DataFrame,
    puts_df: pd.DataFrame,
    dte: int,
    risk_free_rate: float = 0.045
) -> List[Dict[str, Any]]:
    """Build unified Call / Put strike ladder with complete Black-Scholes Greeks."""
    if spot <= 0:
        all_s = []
        if calls_df is not None and not calls_df.empty and "strike" in calls_df.columns:
            all_s.extend(calls_df["strike"].dropna().tolist())
        if puts_df is not None and not puts_df.empty and "strike" in puts_df.columns:
            all_s.extend(puts_df["strike"].dropna().tolist())
        if all_s:
            import pandas as pd
            spot = float(pd.Series(all_s).median())
        else:
            return []

    calls_by_strike = {float(r["strike"]): r for _, r in calls_df.iterrows()} if calls_df is not None and not calls_df.empty else {}
    puts_by_strike = {float(r["strike"]): r for _, r in puts_df.iterrows()} if puts_df is not None and not puts_df.empty else {}

    all_strikes = sorted(list(set(calls_by_strike.keys()).union(set(puts_by_strike.keys()))))
    if not all_strikes:
        return []

    atm_strike = min(all_strikes, key=lambda s: abs(s - spot))
    matrix_rows: List[Dict[str, Any]] = []

    for strike in all_strikes:
        c_row = calls_by_strike.get(strike)
        p_row = puts_by_strike.get(strike)

        # Call data
        call_dict = None
        if c_row is not None:
            bid = float(c_row.get("bid", 0) or 0)
            ask = float(c_row.get("ask", 0) or 0)
            mid = round((bid + ask) / 2.0, 2) if (bid + ask) > 0 else float(c_row.get("lastPrice", 0) or 0)
            iv = float(c_row.get("impliedVolatility", 0) or 0)
            vol = int(c_row.get("volume", 0) or 0)
            oi = int(c_row.get("openInterest", 0) or 0)
            greeks = calculate_black_scholes_greeks(spot, strike, dte, iv, is_call=True, risk_free_rate=risk_free_rate)
            spread = round(max(0.0, ask - bid), 2)
            spread_pct = round((spread / ask) * 100.0, 1) if ask > 0 else 0.0
            call_dict = {
                "contract": str(c_row.get("contractSymbol", "")),
                "bid": bid,
                "ask": ask,
                "mid": mid,
                "last": float(c_row.get("lastPrice", 0) or 0),
                "spread": spread,
                "spread_pct": spread_pct,
                "volume": vol,
                "open_interest": oi,
                "iv_pct": round(iv * 100.0, 1) if iv <= 5.0 else round(iv, 1),
                "inTheMoney": bool(c_row.get("inTheMoney", strike < spot)),
                "delta": greeks.delta,
                "gamma": greeks.gamma,
                "theta": greeks.theta,
                "vega": greeks.vega,
                "rho": greeks.rho,
            }

        # Put data
        put_dict = None
        if p_row is not None:
            bid = float(p_row.get("bid", 0) or 0)
            ask = float(p_row.get("ask", 0) or 0)
            mid = round((bid + ask) / 2.0, 2) if (bid + ask) > 0 else float(p_row.get("lastPrice", 0) or 0)
            iv = float(p_row.get("impliedVolatility", 0) or 0)
            vol = int(p_row.get("volume", 0) or 0)
            oi = int(p_row.get("openInterest", 0) or 0)
            greeks = calculate_black_scholes_greeks(spot, strike, dte, iv, is_call=False, risk_free_rate=risk_free_rate)
            spread = round(max(0.0, ask - bid), 2)
            spread_pct = round((spread / ask) * 100.0, 1) if ask > 0 else 0.0
            put_dict = {
                "contract": str(p_row.get("contractSymbol", "")),
                "bid": bid,
                "ask": ask,
                "mid": mid,
                "last": float(p_row.get("lastPrice", 0) or 0),
                "spread": spread,
                "spread_pct": spread_pct,
                "volume": vol,
                "open_interest": oi,
                "iv_pct": round(iv * 100.0, 1) if iv <= 5.0 else round(iv, 1),
                "inTheMoney": bool(p_row.get("inTheMoney", strike > spot)),
                "delta": greeks.delta,
                "gamma": greeks.gamma,
                "theta": greeks.theta,
                "vega": greeks.vega,
                "rho": greeks.rho,
            }

        matrix_rows.append({
            "strike": strike,
            "is_atm": (strike == atm_strike),
            "is_itm_call": (strike < spot),
            "is_itm_put": (strike > spot),
            "moneyness_pct": round(((strike - spot) / spot) * 100.0, 2),
            "call": call_dict,
            "put": put_dict,
        })

    return matrix_rows
