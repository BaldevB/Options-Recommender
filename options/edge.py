"""Contract edge model: does an option have a realistic chance of paying off?

The legacy ranker scored contracts only on execution quality (delta, spread, liquidity).
This module adds the missing half:

- MarketContext: realized volatility, signal-implied drift, risk-free rate, dividend yield,
  and the next earnings date for the underlying.
- Implied volatility re-solved from the bid/ask mid (yfinance's IV is unreliable when quotes are stale).
- A Monte Carlo simulation that walks the underlying day by day, re-prices the option, and applies
  the same exit rules as the trade plan (+50% target, -50% stop, time stop). This gives a probability
  and expected value that match how the trade is actually managed, and that use the directional signal.
"""

from __future__ import annotations

import logging
import math
import threading
import time
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from config import DEFAULT_CONFIG, EdgeModelConfig

logger = logging.getLogger(__name__)

TRADING_DAYS = 252.0
CAL_DAYS_PER_TRADING_DAY = 365.0 / 252.0
DEFAULT_RISK_FREE = 0.045


# --------------------------------------------------------------------------------------
# Normal distribution + Black-Scholes-Merton (vectorized, no scipy dependency)
# --------------------------------------------------------------------------------------

def _norm_cdf(x: np.ndarray) -> np.ndarray:
    """Standard normal CDF (Abramowitz & Stegun 7.1.26 erf approximation, |error| < 1.5e-7)."""
    x = np.asarray(x, dtype=float)
    z = np.abs(x) / math.sqrt(2.0)
    t = 1.0 / (1.0 + 0.3275911 * z)
    poly = t * (0.254829592 + t * (-0.284496736 + t * (1.421413741 + t * (-1.453152027 + t * 1.061405429))))
    erf = 1.0 - poly * np.exp(-z * z)
    return 0.5 * (1.0 + np.sign(x) * erf)


def bs_price(
    spot: Any, strike: float, t_years: Any, sigma: float, is_call: bool,
    r: float = DEFAULT_RISK_FREE, q: float = 0.0,
) -> np.ndarray:
    """Black-Scholes-Merton price; spot and t_years may be arrays. At t<=0 returns intrinsic value."""
    s = np.asarray(spot, dtype=float)
    t = np.maximum(np.asarray(t_years, dtype=float), 0.0)
    intrinsic = np.maximum(s - strike, 0.0) if is_call else np.maximum(strike - s, 0.0)
    live = t > 1e-6
    if not np.any(live):
        return intrinsic
    sig = max(float(sigma), 1e-4)
    t_safe = np.where(live, t, 1.0)
    s_safe = np.maximum(s, 1e-9)
    sqrt_t = np.sqrt(t_safe)
    d1 = (np.log(s_safe / strike) + (r - q + 0.5 * sig * sig) * t_safe) / (sig * sqrt_t)
    d2 = d1 - sig * sqrt_t
    disc_q = np.exp(-q * t_safe)
    disc_r = np.exp(-r * t_safe)
    if is_call:
        px = s_safe * disc_q * _norm_cdf(d1) - strike * disc_r * _norm_cdf(d2)
    else:
        px = strike * disc_r * _norm_cdf(-d2) - s_safe * disc_q * _norm_cdf(-d1)
    return np.where(live, np.maximum(px, 0.0), intrinsic)


def implied_vol_from_price(
    price: float, spot: float, strike: float, dte: int, is_call: bool,
    r: float = DEFAULT_RISK_FREE, q: float = 0.0,
) -> Optional[float]:
    """Solve implied volatility from an option price by bisection. None if the price is not arbitrage-consistent."""
    if price <= 0 or spot <= 0 or strike <= 0:
        return None
    t = max(dte if dte > 0 else 0.5, 0.5) / 365.0
    lo, hi = 0.01, 5.0
    p_lo = float(bs_price(spot, strike, t, lo, is_call, r, q))
    p_hi = float(bs_price(spot, strike, t, hi, is_call, r, q))
    if not (p_lo <= price <= p_hi):
        return None
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if float(bs_price(spot, strike, t, mid, is_call, r, q)) < price:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-5:
            break
    return 0.5 * (lo + hi)


def solve_underlying_for_option_price(
    target_option_px: float, spot: float, strike: float, t_years: float, sigma: float, is_call: bool,
    r: float = DEFAULT_RISK_FREE, q: float = 0.0,
) -> Optional[float]:
    """Underlying price at which the option is worth target_option_px (option value is monotonic in spot)."""
    lo, hi = spot * 0.2, spot * 5.0
    f = lambda s: float(bs_price(s, strike, t_years, sigma, is_call, r, q)) - target_option_px
    f_lo, f_hi = f(lo), f(hi)
    if is_call and not (f_lo <= 0 <= f_hi):
        return None
    if not is_call and not (f_hi <= 0 <= f_lo):
        return None
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if (fm < 0) == is_call:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-4 * spot:
            break
    return 0.5 * (lo + hi)


def holding_period_trading_days(dte: int) -> int:
    """Time stop used by the trade plan: hold at most 12 trading days, exit by ~21 DTE."""
    return int(min(12, max(3, dte - 14)))


# --------------------------------------------------------------------------------------
# Market rates (cached, network-safe)
# --------------------------------------------------------------------------------------

_RATE_LOCK = threading.Lock()
_RATE_CACHE: Dict[str, Any] = {}
_RATE_TTL = 6 * 3600.0
_DIV_TTL = 24 * 3600.0


def get_risk_free_rate() -> float:
    """13-week T-bill yield (^IRX) as a decimal, cached for 6h. Falls back to 4.5%."""
    with _RATE_LOCK:
        hit = _RATE_CACHE.get("rf")
        if hit and time.time() - hit[0] < _RATE_TTL:
            return hit[1]
    rate = DEFAULT_RISK_FREE
    try:
        import yfinance as yf
        px = float(getattr(yf.Ticker("^IRX").fast_info, "last_price", 0.0) or 0.0)
        if 0.0 < px < 20.0:  # quoted in percent
            rate = px / 100.0
    except Exception as exc:
        logger.debug("Risk-free rate lookup failed, using default: %s", exc)
    with _RATE_LOCK:
        _RATE_CACHE["rf"] = (time.time(), rate)
    return rate


def get_dividend_yield(symbol: str, spot: float) -> float:
    """Trailing-12-month dividend yield as a decimal, cached for 24h. 0.0 when unknown."""
    key = f"div_{symbol}"
    with _RATE_LOCK:
        hit = _RATE_CACHE.get(key)
        if hit and time.time() - hit[0] < _DIV_TTL:
            return hit[1]
    yld = 0.0
    try:
        import yfinance as yf
        divs = yf.Ticker(symbol).dividends
        if divs is not None and len(divs) > 0 and spot > 0:
            idx = pd.to_datetime(divs.index)
            cutoff = pd.Timestamp.now(tz=idx.tz) - pd.Timedelta(days=365)
            yld = float(divs[idx >= cutoff].sum()) / spot
            yld = float(np.clip(yld, 0.0, 0.15))
    except Exception as exc:
        logger.debug("Dividend lookup failed for %s: %s", symbol, exc)
    with _RATE_LOCK:
        _RATE_CACHE[key] = (time.time(), yld)
    return yld


# --------------------------------------------------------------------------------------
# Market context
# --------------------------------------------------------------------------------------

@dataclass
class MarketContext:
    """Everything the edge model needs to know about the underlying, beyond the option chain."""
    symbol: str
    spot: float
    realized_vol: float                 # annualized, decimal (0 if unknown)
    atr_pct: float                      # average true range as % of spot (daily)
    daily_drift: float                  # signed daily log drift implied by the signal
    signal_confidence: float = 0.0
    risk_free_rate: float = DEFAULT_RISK_FREE
    dividend_yield: float = 0.0
    earnings_date: Optional[date] = None
    cfg: EdgeModelConfig = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.cfg is None:
            self.cfg = DEFAULT_CONFIG.edge


def realized_volatility(hist: Optional[pd.DataFrame]) -> float:
    """Annualized realized vol blending 20- and 60-day windows of log returns (0 if not computable)."""
    if hist is None or len(hist) < 12 or "Close" not in hist:
        return 0.0
    closes = pd.to_numeric(hist["Close"], errors="coerce").dropna().values
    closes = closes[closes > 0]
    if len(closes) < 12:
        return 0.0
    lr = np.diff(np.log(closes))
    v20 = float(np.std(lr[-20:], ddof=1)) if len(lr) >= 10 else 0.0
    v60 = float(np.std(lr[-60:], ddof=1)) if len(lr) >= 30 else v20
    daily = math.sqrt(0.5 * v20 * v20 + 0.5 * v60 * v60)
    return daily * math.sqrt(TRADING_DAYS) if np.isfinite(daily) else 0.0


def average_true_range_pct(hist: Optional[pd.DataFrame], window: int = 14) -> float:
    """ATR(14) as a percentage of the last close."""
    if hist is None or len(hist) < window + 1 or not {"High", "Low", "Close"}.issubset(hist.columns):
        return 0.0
    h, l, c = hist["High"].astype(float), hist["Low"].astype(float), hist["Close"].astype(float)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = float(tr.tail(window).mean())
    last = float(c.iloc[-1])
    return round(atr / last * 100.0, 2) if last > 0 and np.isfinite(atr) else 0.0


def _parse_date(value: Any) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def build_market_context(
    symbol: str,
    spot: float,
    hist: Optional[pd.DataFrame],
    signal: Any = None,
    earnings_info: Optional[Dict[str, Any]] = None,
    cfg: Optional[EdgeModelConfig] = None,
    fetch_rates: bool = True,
) -> MarketContext:
    """Assemble the market context for one underlying. Never raises; missing pieces fall back to neutral values."""
    cfg = cfg or DEFAULT_CONFIG.edge
    confidence = float(getattr(signal, "confidence", 0.0) or 0.0) if signal is not None else 0.0
    bias = str(getattr(getattr(signal, "bias", None), "value", getattr(signal, "bias", "")) or "").upper()
    sign = 1.0 if bias == "BULLISH" else (-1.0 if bias == "BEARISH" else 0.0)
    if earnings_info is None and signal is not None:
        earnings_info = getattr(signal, "earnings_info", None)
    return MarketContext(
        symbol=symbol.upper(),
        spot=float(spot),
        realized_vol=realized_volatility(hist),
        atr_pct=average_true_range_pct(hist),
        daily_drift=sign * min(max(confidence, 0.0), 1.0) * cfg.max_signal_drift_daily,
        signal_confidence=confidence,
        risk_free_rate=get_risk_free_rate() if fetch_rates else DEFAULT_RISK_FREE,
        dividend_yield=get_dividend_yield(symbol, spot) if fetch_rates else 0.0,
        earnings_date=_parse_date((earnings_info or {}).get("next_earnings_date")),
        cfg=cfg,
    )


def vol_regime(iv: float, realized_vol: float, cfg: Optional[EdgeModelConfig] = None) -> Dict[str, Any]:
    """Classify implied vs realized volatility for this stock: RICH favours spreads, CHEAP favours long options."""
    cfg = cfg or DEFAULT_CONFIG.edge
    if realized_vol <= 0 or iv <= 0:
        return {"iv_hv_ratio": None, "regime": "UNKNOWN"}
    ratio = iv / realized_vol
    regime = "RICH" if ratio >= cfg.rich_iv_hv_ratio else ("CHEAP" if ratio <= cfg.cheap_iv_hv_ratio else "FAIR")
    return {"iv_hv_ratio": round(ratio, 2), "regime": regime}


def spans_earnings(expiration: str, earnings: Optional[date]) -> bool:
    """True when the earnings date falls on or before expiration (the option holds the event and the IV crush)."""
    exp = _parse_date(expiration)
    if not exp or not earnings:
        return False
    return earnings <= exp and earnings >= date.today()


# --------------------------------------------------------------------------------------
# Monte Carlo exit simulation
# --------------------------------------------------------------------------------------

@dataclass
class ExitSimulation:
    prob_target: float          # hit take-profit before stop
    prob_stop: float            # hit stop first
    prob_time_exit: float       # neither; closed at the time stop
    prob_profit: float          # finished with a positive P&L (target + profitable time exits)
    expected_pnl: float         # $ per contract, after half-spread exit slippage
    expected_return_pct: float  # expected_pnl / premium paid
    holding_days: int


def simulate_exit_outcomes(
    spot: float,
    strike: float,
    entry_px: float,
    iv: float,
    dte: int,
    is_call: bool,
    ctx: MarketContext,
    half_spread: float = 0.0,
) -> Optional[ExitSimulation]:
    """Simulate the underlying with realized vol + signal drift and apply the trade plan's exit rules."""
    cfg = ctx.cfg
    if spot <= 0 or entry_px <= 0 or iv <= 0 or dte <= 0:
        return None
    sigma_stock = ctx.realized_vol if ctx.realized_vol > 0 else iv
    hold = max(1, min(holding_period_trading_days(dte), int(dte / CAL_DAYS_PER_TRADING_DAY)))
    n = max(200, int(cfg.simulations))
    rng = np.random.default_rng(cfg.seed)

    # Several checks per trading day approximate continuously-monitored bracket orders; with only
    # daily checks a fast-moving option overshoots its target and the fill understates the payoff.
    steps_per_day = 4
    n_steps = hold * steps_per_day
    step_sigma = sigma_stock / math.sqrt(TRADING_DAYS * steps_per_day)
    shocks = rng.standard_normal((n, n_steps))
    log_paths = np.cumsum(ctx.daily_drift / steps_per_day + step_sigma * shocks, axis=1)
    s_paths = spot * np.exp(log_paths)

    r, q = ctx.risk_free_rate, ctx.dividend_yield
    t0 = max(dte, 0.5) / 365.0
    model_entry = float(bs_price(spot, strike, t0, iv, is_call, r, q))
    if model_entry <= 0:
        return None
    anchor = entry_px / model_entry  # keep simulated prices consistent with the actual entry quote

    tp = entry_px * cfg.take_profit_mult
    sl = entry_px * cfg.stop_loss_mult
    exit_px = np.full(n, np.nan)
    outcome = np.zeros(n, dtype=np.int8)  # 1 target, -1 stop, 0 open
    for d in range(n_steps):
        t_left = max(dte - (d + 1) / steps_per_day * CAL_DAYS_PER_TRADING_DAY, 0.0) / 365.0
        val = bs_price(s_paths[:, d], strike, t_left, iv, is_call, r, q) * anchor
        open_mask = outcome == 0
        hit_tp = open_mask & (val >= tp)
        hit_sl = open_mask & ~hit_tp & (val <= sl)
        outcome[hit_tp] = 1
        exit_px[hit_tp] = tp  # resting limit order fills at the target
        outcome[hit_sl] = -1
        # Bracket orders work intraday, so both legs fill near their trigger levels (daily steps would
        # otherwise cap the upside at the target but let the stop fill at the end-of-day value).
        exit_px[hit_sl] = max(sl - half_spread, 0.0)  # stop-market pays the spread
        if d == n_steps - 1:
            still = outcome == 0
            exit_px[still] = np.maximum(val[still] - half_spread, 0.0)

    pnl = (exit_px - entry_px) * 100.0
    p_tp = float(np.mean(outcome == 1))
    p_sl = float(np.mean(outcome == -1))
    exp_pnl = float(np.mean(pnl))
    return ExitSimulation(
        prob_target=round(p_tp * 100.0, 1),
        prob_stop=round(p_sl * 100.0, 1),
        prob_time_exit=round((1.0 - p_tp - p_sl) * 100.0, 1),
        prob_profit=round(float(np.mean(pnl > 0)) * 100.0, 1),
        expected_pnl=round(exp_pnl, 2),
        expected_return_pct=round(exp_pnl / (entry_px * 100.0) * 100.0, 1),
        holding_days=hold,
    )


def move_metrics(
    spot: float, breakeven: float, theta: float, gamma: float, dte: int, is_call: bool, ctx: MarketContext,
) -> Dict[str, Optional[float]]:
    """Required move vs typical move over the holding period, and daily theta vs daily gamma gain.

    theta_vs_gamma_ratio = |theta| / (0.5 * gamma * (spot * daily realized vol)^2). It is ~1 when implied
    vol equals realized vol; above 1 the stock's typical moves don't pay for the time decay.
    """
    if ctx.realized_vol <= 0 or spot <= 0:
        return {"expected_move_pct": None, "move_coverage_ratio": None, "theta_vs_gamma_ratio": None}
    hold = holding_period_trading_days(dte)
    exp_move_pct = ctx.realized_vol * math.sqrt(hold / TRADING_DAYS) * 100.0
    req = ((breakeven - spot) / spot * 100.0) if is_call else ((spot - breakeven) / spot * 100.0)
    coverage = (exp_move_pct / req) if req > 0.05 else 10.0  # already past breakeven -> very high coverage
    daily_move = spot * ctx.realized_vol / math.sqrt(365.0)  # theta is per calendar day
    gamma_gain = 0.5 * abs(gamma) * daily_move * daily_move
    theta_ratio = (abs(theta) / gamma_gain) if gamma_gain > 0 else None
    return {
        "expected_move_pct": round(exp_move_pct, 2),
        "move_coverage_ratio": round(min(coverage, 10.0), 2),
        "theta_vs_gamma_ratio": round(theta_ratio, 2) if theta_ratio is not None else None,
    }


def edge_score_from(sim: Optional[ExitSimulation], coverage: Optional[float]) -> float:
    """0-100 edge score: mostly simulated return on premium, partly breakeven move coverage."""
    if sim is None:
        return 50.0
    ret = float(np.clip((sim.expected_return_pct + 25.0) / 50.0, 0.0, 1.0))  # -25%..+25% -> 0..1
    cov = float(np.clip((coverage or 1.0) / 2.0, 0.0, 1.0))                  # 0x..2x -> 0..1
    return round((0.75 * ret + 0.25 * cov) * 100.0, 1)
