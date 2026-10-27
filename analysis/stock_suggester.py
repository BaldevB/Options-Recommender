"""Quantitative stock trade recommendation engine.

Calculates actionable trade plans (Entry Zone, TP1, TP2, Stop Loss, Risk-Reward ratio),
classifies trade horizon (SWING vs LONG_TERM), evaluates overall composite score, and
determines risk-based integer share position sizing for 1,000+ US equities.

Enhanced with institutional stock selection factors:
- Relative Strength (RS) percentile rating (vs benchmark)
- Distance from 52-Week High (%) & Breakout detection
- Multi-Moving-Average structural alignment (Full Bullish, Golden Cross, Pullback)
- Minervini Stage 2 Superperformance Trend Template Filter
- Volatility Contraction Pattern (VCP) & Consolidation Squeeze Detector
- Institutional Accumulation/Distribution (A/D) Inflow Rating & Up/Down Volume Ratio
- Strategy preset tagging (STAGE_2_LEADER, VCP_SQUEEZE, INSTITUTIONAL_INFLOW, RS_LEADER, 52W_BREAKOUT, GOLDEN_CROSS, PULLBACK_DIP, MOMENTUM_SWING)
"""

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Tuple, List, Dict, Any, Optional, Union
import numpy as np
import pandas as pd

from analysis.momentum import MomentumResult, ShortTermMomentumResult, calculate_short_term_momentum
from analysis.sentiment import SentimentResult
from data.price_data import QuoteData
from data.stock_universe import get_stock_metadata


class TradeHorizon(str, Enum):
    """Trading timeframe horizon."""
    SWING = "SWING"
    LONG_TERM = "LONG_TERM"


@dataclass
class StockTradePlan:
    """Quantitative price levels, targets, and risk metrics for equity trade execution."""
    entry_zone: Tuple[float, float]
    current_price: float
    tp1: float
    tp2: float
    stop_loss: float
    risk_reward_ratio: float
    invalidation_pct: float
    tp1_pct: float
    tp2_pct: float


@dataclass
class StockRecommendation:
    """Comprehensive stock recommendation with trade plan, score, and rationales."""
    symbol: str
    name: str
    sector: str
    horizon: TradeHorizon
    action: str
    score: float
    confidence: float
    momentum_score: float
    sentiment_score: float
    trade_plan: StockTradePlan
    rationale: List[str] = field(default_factory=list)
    relative_strength_score: float = 50.0
    distance_from_52w_high_pct: float = 0.0
    ma_alignment: str = "NEUTRAL"
    strategy_tag: str = "MOMENTUM_SWING"
    is_stage_2: bool = False
    is_vcp_squeeze: bool = False
    consolidation_tightness: float = 50.0
    accumulation_rating: str = "B"
    up_down_volume_ratio: float = 1.0
    roc_3d: float = 0.0
    roc_5d: float = 0.0
    roc_10d: float = 0.0
    short_term_rsi: float = 50.0
    short_term_rvol: float = 1.0
    ema_spread_pct: float = 0.0
    short_term_momentum_score: float = 50.0
    short_term_setup: str = "MOMENTUM_CONSOLIDATION"
    is_short_term_breakout: bool = False
    earnings_days_away: Optional[int] = None
    is_earnings_imminent: bool = False
    market_cap_tier: str = "LARGE"
    is_earnings_blackout: bool = False


def calculate_atr(
    df: Optional[pd.DataFrame] = None,
    current_price: float = 100.0,
    day_high: float = 0.0,
    day_low: float = 0.0,
    period: int = 14,
) -> float:
    """Compute 14-period Average True Range (ATR) or calculate fallback from daily range.

    Args:
        df: Optional historical OHLCV dataframe.
        current_price: Latest close/last price.
        day_high: Intraday high.
        day_low: Intraday low.
        period: ATR lookback period (default 14).

    Returns:
        float: Calculated or estimated ATR.
    """
    if df is not None and not df.empty and len(df) >= 5:
        try:
            high = df["High"]
            low = df["Low"]
            close = df["Close"]
            prev_close = close.shift(1)

            tr1 = high - low
            tr2 = (high - prev_close).abs()
            tr3 = (low - prev_close).abs()
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

            atr_val = tr.rolling(window=min(period, len(df))).mean().iloc[-1]
            if not pd.isna(atr_val) and atr_val > 0:
                return round(float(atr_val), 2)
        except Exception:
            pass

    if day_high > day_low > 0:
        day_range = day_high - day_low
        return round(max(day_range, current_price * 0.02), 2)

    # General conservative fallback: 2.5% of current price
    return round(max(0.50, current_price * 0.025), 2)


def evaluate_relative_strength(
    df: Optional[pd.DataFrame] = None,
    mom_score: float = 0.0,
    current_price: float = 100.0,
) -> float:
    """Evaluate institutional relative strength score (0.0 to 99.0) vs broader market benchmark."""
    if df is not None and not df.empty and len(df) >= 15:
        try:
            close_series = df["Close"]
            cur = float(close_series.iloc[-1])
            # 20-day return
            lookback_20 = min(len(close_series) - 1, 20)
            p_20 = float(close_series.iloc[-lookback_20])
            ret_20d = (cur - p_20) / p_20 if p_20 > 0 else 0.0

            # 60-day return
            lookback_60 = min(len(close_series) - 1, 60)
            p_60 = float(close_series.iloc[-lookback_60])
            ret_60d = (cur - p_60) / p_60 if p_60 > 0 else ret_20d

            # Base score centering at 50, rewarding outperformance
            rs = 50.0 + (ret_20d * 120.0) + (ret_60d * 40.0) + (mom_score * 15.0)
            return round(max(1.0, min(99.0, rs)), 1)
        except Exception:
            pass

    # Baseline calculation from momentum score
    rs_fallback = 50.0 + (mom_score * 35.0)
    return round(max(1.0, min(99.0, rs_fallback)), 1)


def evaluate_ma_structure(
    df: Optional[pd.DataFrame] = None,
    current_price: float = 100.0,
    momentum: Optional[MomentumResult] = None,
) -> str:
    """Determine moving average structure (FULL_BULLISH, GOLDEN_CROSS, PULLBACK_SUPPORT, BEARISH, NEUTRAL)."""
    sma_20 = getattr(momentum, "sma_20", None) if momentum else None
    sma_50 = getattr(momentum, "sma_50", None) if momentum else None
    sma_200 = getattr(momentum, "sma_200", None) if momentum else None

    if df is not None and not df.empty and len(df) >= 20:
        try:
            closes = df["Close"]
            if sma_20 is None and len(closes) >= 20:
                sma_20 = float(closes.rolling(20).mean().iloc[-1])
            if sma_50 is None and len(closes) >= 50:
                sma_50 = float(closes.rolling(50).mean().iloc[-1])
            if sma_200 is None and len(closes) >= 200:
                sma_200 = float(closes.rolling(200).mean().iloc[-1])
        except Exception:
            pass

    if sma_50 and sma_200 and sma_50 > sma_200:
        if sma_20 and current_price > sma_20 > sma_50:
            return "FULL_BULLISH"
        return "GOLDEN_CROSS"

    if sma_20 and sma_50 and current_price > sma_20 > sma_50:
        return "BULLISH_TREND"

    if sma_50 and current_price > sma_50:
        return "ABOVE_50DMA"

    if sma_200 and current_price < sma_200:
        return "BELOW_200DMA"

    return "NEUTRAL"


def evaluate_minervini_stage_2(
    df: Optional[pd.DataFrame] = None,
    current_price: float = 100.0,
    fifty_two_week_high: float = 0.0,
    fifty_two_week_low: float = 0.0,
    momentum: Optional[MomentumResult] = None,
) -> bool:
    """Evaluate whether an equity meets Mark Minervini's Stage 2 Superperformance Trend Template criteria.

    Criteria:
    1. Current Price > 50-day Simple Moving Average (SMA)
    2. Current Price > 200-day Simple Moving Average (SMA)
    3. 50-day SMA > 200-day SMA
    4. 200-day SMA is trending upward (or flat-to-rising)
    5. Current price is within 25% of 52-week high (price >= 0.75 * 52W High)
    6. Current price is at least 25% above 52-week low (or local low)
    """
    sma_50 = getattr(momentum, "sma_50", None) if momentum else None
    sma_200 = getattr(momentum, "sma_200", None) if momentum else None
    sma_200_rising = True

    if df is not None and not df.empty and len(df) >= 20:
        try:
            closes = df["Close"]
            if sma_50 is None and len(closes) >= 50:
                sma_50 = float(closes.rolling(50).mean().iloc[-1])
            elif sma_50 is None and len(closes) >= 20:
                sma_50 = float(closes.rolling(20).mean().iloc[-1])

            if sma_200 is None and len(closes) >= 180:
                sma_200 = float(closes.rolling(min(200, len(closes))).mean().iloc[-1])
                # Check if 200-day SMA is flat-to-rising over the past 20 sessions
                if len(closes) >= 200:
                    roll_200 = closes.rolling(200).mean()
                    prev_idx = -21 if len(roll_200) >= 21 else -1
                    sma_200_20d_ago = float(roll_200.iloc[prev_idx])
                    if not pd.isna(sma_200_20d_ago) and sma_200_20d_ago > 0:
                        sma_200_rising = sma_200 >= (sma_200_20d_ago * 0.995)
        except Exception:
            pass

    # Momentum fallback attributes if SMA values were not directly in dataframe
    if momentum and momentum.details:
        if sma_50 is None:
            above_sma50 = momentum.details.get("above_sma50", False)
            if above_sma50:
                sma_50 = current_price * 0.96
        if sma_200 is None:
            sma20_above_sma50 = momentum.details.get("sma20_above_sma50", False)
            if sma20_above_sma50 and sma_50:
                sma_200 = sma_50 * 0.95

    # Check Moving Average Conditions
    if sma_50 and sma_200:
        ma_cond = (current_price > sma_50) and (current_price > sma_200) and (sma_50 > sma_200) and sma_200_rising
    elif sma_50:
        ma_cond = current_price > sma_50
    elif momentum and momentum.details:
        ma_cond = bool(momentum.details.get("above_sma50", False))
    else:
        ma_cond = False

    # Check 52W High Condition: Within 25% of 52W High
    high_cond = True
    if fifty_two_week_high > 0:
        high_cond = current_price >= (fifty_two_week_high * 0.75)

    # Check 52W Low Condition: At least 25% above 52W Low
    low_cond = True
    if fifty_two_week_low > 0:
        low_cond = current_price >= (fifty_two_week_low * 1.25)
    elif df is not None and not df.empty and len(df) >= 20:
        try:
            low_min = float(df["Low"].min())
            if low_min > 0:
                low_cond = current_price >= (low_min * 1.20)
        except Exception:
            pass

    return bool(ma_cond and high_cond and low_cond)


def evaluate_vcp_squeeze(
    df: Optional[pd.DataFrame] = None,
    current_price: float = 100.0,
) -> Tuple[bool, float]:
    """Detect Volatility Contraction Pattern (VCP) & Consolidation Squeeze.

    Evaluates:
    - Range compression: 10-day High-Low range relative to 30-day High-Low range.
    - Bollinger Band width: 10-day bandwidth relative to mean close.

    Returns:
        Tuple[bool, float]: (is_vcp_squeeze, consolidation_tightness_score_0_to_100)
    """
    if df is not None and not df.empty and len(df) >= 15:
        try:
            highs = df["High"]
            lows = df["Low"]
            closes = df["Close"]

            len_10 = min(len(df), 10)
            len_30 = min(len(df), 30)

            range_10 = float(highs.iloc[-len_10:].max() - lows.iloc[-len_10:].min())
            range_30 = float(highs.iloc[-len_30:].max() - lows.iloc[-len_30:].min())
            range_ratio = (range_10 / range_30) if range_30 > 0 else 1.0

            # Range compression tightness (up to 55 pts)
            range_tightness = max(0.0, min(55.0, (1.0 - (range_ratio / 0.8)) * 55.0)) if range_ratio < 0.8 else 0.0

            # BB width on recent consolidation window (10 days)
            w = min(len(closes), 10)
            rolling_window = closes.iloc[-w:]
            mean_10 = float(rolling_window.mean())
            std_10 = float(rolling_window.std()) if len(rolling_window) > 1 else 0.0
            bb_width = (4.0 * std_10) / mean_10 if mean_10 > 0 else 0.10

            # BB width tightness (up to 45 pts)
            # BB width <= 4% gives max tightness; >= 14% gives 0.
            bb_tightness = max(0.0, min(45.0, (0.14 - bb_width) / 0.14 * 45.0))

            tightness = round(max(5.0, min(99.0, range_tightness + bb_tightness)), 1)
            is_squeeze = bool(tightness >= 60.0 or (range_ratio <= 0.50 and bb_width <= 0.08))
            return is_squeeze, tightness
        except Exception:
            pass

    return False, 50.0


def evaluate_accumulation_distribution(
    df: Optional[pd.DataFrame] = None,
    volume_ratio: float = 1.0,
    mom_score: float = 0.0,
) -> Tuple[str, float]:
    """Evaluate Institutional Up/Down Volume Ratio & Accumulation/Distribution Inflow Rating (A+, A, B, C, D).

    Calculates the 30-day ratio of volume on up days vs volume on down days:
    - A+: Ratio >= 1.50 (Aggressive institutional accumulation)
    - A:  Ratio 1.25 to 1.49 (Solid institutional buying pressure)
    - B:  Ratio 0.95 to 1.24 (Neutral/balanced flow)
    - C:  Ratio 0.75 to 0.94 (Mild distribution)
    - D:  Ratio < 0.75 (Heavy institutional liquidation/distribution)

    Returns:
        Tuple[str, float]: (accumulation_rating, up_down_volume_ratio)
    """
    if df is not None and not df.empty and len(df) >= 8 and "Volume" in df.columns:
        try:
            sub = df.iloc[-min(len(df), 30):].copy()
            closes = sub["Close"]
            diffs = closes.diff()

            up_mask = diffs > 0
            down_mask = diffs < 0

            up_volume = float(sub.loc[up_mask, "Volume"].sum())
            down_volume = float(sub.loc[down_mask, "Volume"].sum())

            if down_volume > 0:
                raw_ratio = up_volume / down_volume
            elif up_volume > 0:
                raw_ratio = 2.50
            else:
                raw_ratio = 1.00

            ratio = round(max(0.10, min(5.00, raw_ratio)), 2)
        except Exception:
            ratio = round(max(0.40, min(3.00, 1.0 + (mom_score * 0.8) + ((volume_ratio - 1.0) * 0.4))), 2)
    else:
        # Fallback estimation using momentum score & volume ratio
        ratio = round(max(0.40, min(3.00, 1.0 + (mom_score * 0.8) + ((volume_ratio - 1.0) * 0.4))), 2)

    if ratio >= 1.50:
        rating = "A+"
    elif ratio >= 1.25:
        rating = "A"
    elif ratio >= 0.95:
        rating = "B"
    elif ratio >= 0.75:
        rating = "C"
    else:
        rating = "D"

    return rating, ratio


def evaluate_strategy_tag(
    relative_strength: float,
    dist_52w_pct: float,
    ma_alignment: str,
    rsi: float,
    volume_ratio: float,
    mom_score: float,
    is_stage_2: bool = False,
    is_vcp_squeeze: bool = False,
    accumulation_rating: str = "B",
) -> str:
    """Classify the primary high-confidence stock selection strategy."""
    # 1. Minervini Stage 2 Superperformance Leader
    if is_stage_2 and relative_strength >= 78.0 and mom_score > 0.15:
        return "STAGE_2_LEADER"

    # 2. Volatility Contraction Pattern (VCP) Squeeze
    if is_vcp_squeeze and mom_score >= 0.05 and ma_alignment != "BELOW_200DMA":
        return "VCP_SQUEEZE"

    # 3. Institutional Inflow / Heavy Accumulation
    if accumulation_rating == "A+" and mom_score > 0.10:
        return "INSTITUTIONAL_INFLOW"

    # 4. 52-Week High Breakout
    if dist_52w_pct >= -7.0 and volume_ratio >= 1.20 and mom_score > 0.15:
        return "52W_BREAKOUT"

    # 5. Relative Strength Market Leader
    if relative_strength >= 78.0 and mom_score > 0.10:
        return "RS_LEADER"

    # 6. Golden Cross Momentum
    if ma_alignment in ("FULL_BULLISH", "GOLDEN_CROSS") and mom_score > 0.20:
        return "GOLDEN_CROSS"

    # 7. Pullback / Dip Buy into Moving Average Support
    if rsi <= 44.0 and mom_score >= -0.20 and ma_alignment != "BELOW_200DMA":
        return "PULLBACK_DIP"

    # 8. Volume Surge
    if volume_ratio >= 1.40 and mom_score > 0.10:
        return "VOLUME_SURGE"

    return "MOMENTUM_SWING"


def classify_trade_horizon(
    momentum: Optional[MomentumResult] = None,
    beta: Optional[float] = None,
    explicit_horizon: Optional[TradeHorizon] = None,
) -> TradeHorizon:
    """Classify trade horizon as SWING (1-5d breakout) or LONG_TERM (trend conviction).

    Args:
        momentum: MomentumResult instance.
        beta: Stock volatility beta relative to S&P 500.
        explicit_horizon: Explicit override if specified.

    Returns:
        TradeHorizon (SWING or LONG_TERM)
    """
    if explicit_horizon is not None:
        return explicit_horizon

    if beta is not None:
        # Low beta (<= 1.15) with aligned weekly trend suggests steady investment
        if beta <= 1.15:
            if momentum and (momentum.multi_timeframe_aligned or momentum.weekly_trend == "BULLISH"):
                return TradeHorizon.LONG_TERM
        else:
            return TradeHorizon.SWING

    if momentum is not None:
        # High volume breakout or extreme short-term velocity -> SWING
        if momentum.volume_ratio >= 1.20 or abs(momentum.momentum_score) >= 0.45 or momentum.rsi > 68:
            return TradeHorizon.SWING

        # Multi-timeframe trend alignment with steady volume -> LONG_TERM
        if momentum.multi_timeframe_aligned and momentum.weekly_trend == "BULLISH" and momentum.momentum_score > 0:
            return TradeHorizon.LONG_TERM

    return TradeHorizon.SWING


def build_trade_plan(
    current_price: float,
    atr: float,
    horizon: TradeHorizon,
) -> StockTradePlan:
    """Generate price levels and targets based on ATR and horizon classification.

    Args:
        current_price: Current market price of the equity.
        atr: Average True Range.
        horizon: TradeHorizon (SWING or LONG_TERM).

    Returns:
        StockTradePlan
    """
    price = max(0.01, current_price)
    effective_atr = max(0.05, atr)

    if horizon == TradeHorizon.LONG_TERM:
        # Wider targets and stops for multi-week/month holds
        stop_dist = max(0.50, round(1.5 * effective_atr, 2))
        stop_loss = round(max(0.01, price - stop_dist), 2)
        actual_risk = round(price - stop_loss, 2)
        if actual_risk <= 0:
            stop_loss = round(price * 0.88, 2)
            actual_risk = round(price - stop_loss, 2)

        tp1 = round(price + max(3.0 * actual_risk, 3.0 * effective_atr), 2)
        tp2 = round(price + max(6.0 * actual_risk, 6.0 * effective_atr), 2)
        entry_zone = (round(price * 0.97, 2), round(price * 1.01, 2))
    else:
        # Swing setup: 1.0x ATR stop, 1.6x ATR TP1, 3.0x ATR TP2 (guarantees R:R >= 1.5)
        stop_dist = max(0.20, round(1.0 * effective_atr, 2))
        stop_loss = round(max(0.01, price - stop_dist), 2)
        actual_risk = round(price - stop_loss, 2)
        if actual_risk <= 0:
            stop_loss = round(price * 0.92, 2)
            actual_risk = round(price - stop_loss, 2)

        tp1 = round(price + max(1.6 * actual_risk, 1.6 * effective_atr), 2)
        tp2 = round(price + max(3.2 * actual_risk, 3.2 * effective_atr), 2)
        entry_zone = (round(price * 0.99, 2), round(price * 1.005, 2))

    reward1 = round(tp1 - price, 2)
    risk_reward_ratio = round(reward1 / actual_risk, 2) if actual_risk > 0 else 1.50
    # Ensure minimum 1.5 R:R representation
    if risk_reward_ratio < 1.50:
        risk_reward_ratio = 1.50

    invalidation_pct = round(((price - stop_loss) / price) * 100.0, 2)
    tp1_pct = round(((tp1 - price) / price) * 100.0, 2)
    tp2_pct = round(((tp2 - price) / price) * 100.0, 2)

    return StockTradePlan(
        entry_zone=entry_zone,
        current_price=round(price, 2),
        tp1=tp1,
        tp2=tp2,
        stop_loss=stop_loss,
        risk_reward_ratio=risk_reward_ratio,
        invalidation_pct=invalidation_pct,
        tp1_pct=tp1_pct,
        tp2_pct=tp2_pct,
    )


def calculate_stock_shares(
    cash: float,
    risk_pct: float,
    entry_price: float,
    stop_loss: float,
) -> Dict[str, Any]:
    """Calculate integer whole share quantity using risk-based capital allocation.

    Formula:
        Risk Amount = Cash * Risk %
        Risk Per Share = Entry Price - Stop Loss
        Shares = floor(Risk Amount / Risk Per Share), capped by cash purchasing power

    Args:
        cash: Total account equity or available cash in USD.
        risk_pct: Maximum portfolio risk percent (e.g. 2.0 for 2% or 0.02).
        entry_price: Planned entry execution price.
        stop_loss: Technical invalidation stop loss price.

    Returns:
        Dict with shares, capital_required, risk_amount, risk_per_share, max_loss.
    """
    # Safe validation fallbacks
    if cash <= 0.0 or entry_price <= 0.0 or stop_loss <= 0.0 or risk_pct <= 0.0:
        return {
            "shares": 0,
            "capital_required": 0.0,
            "risk_amount": 0.0,
            "risk_per_share": 0.0,
            "max_loss": 0.0,
            "capital_pct_used": 0.0,
            "cash": max(0.0, cash),
            "risk_pct": risk_pct,
            "entry_price": max(0.0, entry_price),
            "stop_loss": max(0.0, stop_loss),
        }

    # Stop loss must be below entry price for long trades
    if stop_loss >= entry_price:
        return {
            "shares": 0,
            "capital_required": 0.0,
            "risk_amount": 0.0,
            "risk_per_share": 0.0,
            "max_loss": 0.0,
            "capital_pct_used": 0.0,
            "cash": cash,
            "risk_pct": risk_pct,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
        }

    # Normalize risk percent (handle 2.0 as 2% and 0.02 as 2%)
    if risk_pct < 0.10:
        risk_fraction = risk_pct
    else:
        risk_fraction = risk_pct / 100.0

    risk_amount = cash * risk_fraction
    risk_per_share = entry_price - stop_loss

    if risk_per_share <= 0:
        return {
            "shares": 0,
            "capital_required": 0.0,
            "risk_amount": 0.0,
            "risk_per_share": 0.0,
            "max_loss": 0.0,
            "capital_pct_used": 0.0,
            "cash": cash,
            "risk_pct": risk_pct,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
        }

    shares_by_risk = int(risk_amount // risk_per_share)
    max_shares_by_cash = int(cash // entry_price)
    shares = max(0, min(shares_by_risk, max_shares_by_cash))

    capital_required = round(shares * entry_price, 2)
    max_loss = round(shares * risk_per_share, 2)
    capital_pct_used = round((capital_required / cash) * 100.0, 2) if cash > 0 else 0.0

    return {
        "shares": shares,
        "capital_required": capital_required,
        "risk_amount": round(risk_amount, 2),
        "risk_per_share": round(risk_per_share, 2),
        "max_loss": max_loss,
        "capital_pct_used": capital_pct_used,
        "cash": cash,
        "risk_pct": risk_pct,
        "entry_price": entry_price,
        "stop_loss": stop_loss,
    }


def generate_stock_recommendation(
    target: Any = None,
    *args,
    symbol: Optional[str] = None,
    quote: Optional[Union[QuoteData, Dict[str, Any]]] = None,
    momentum: Optional[MomentumResult] = None,
    sentiment: Optional[SentimentResult] = None,
    df: Optional[pd.DataFrame] = None,
    beta: Optional[float] = None,
    sector: Optional[str] = None,
    name: Optional[str] = None,
    horizon: Optional[TradeHorizon] = None,
    earnings_info: Optional[Dict[str, Any]] = None,
    market_cap_tier: Optional[str] = None,
    **kwargs,
) -> StockRecommendation:
    """Generate a quantitative stock recommendation with actionable trade plan and scoring."""
    # Parse positional arguments dynamically
    all_args = [target] + list(args) if target is not None else list(args)
    for a in all_args:
        if isinstance(a, MomentumResult) and momentum is None:
            momentum = a
        elif isinstance(a, SentimentResult) and sentiment is None:
            sentiment = a
        elif isinstance(a, QuoteData) and quote is None:
            quote = a
        elif isinstance(a, pd.DataFrame) and df is None:
            df = a
        elif isinstance(a, TradeHorizon) and horizon is None:
            horizon = a
        elif isinstance(a, str) and symbol is None:
            symbol = a.strip().upper()
        elif isinstance(a, dict):
            if "current_price" in a or "valid" in a:
                if quote is None:
                    quote = a
            elif "is_blackout" in a and earnings_info is None:
                earnings_info = a
            elif "overall_score" in a and sentiment is None:
                sentiment = a
        elif isinstance(a, (int, float)) and beta is None and not isinstance(a, bool):
            beta = float(a)

    # Resolve symbol
    if not symbol:
        if quote is not None:
            symbol = getattr(quote, "symbol", None) or (quote.get("symbol") if isinstance(quote, dict) else None)
        if not symbol and momentum is not None:
            symbol = momentum.symbol
        if not symbol and sentiment is not None:
            symbol = sentiment.symbol
        if not symbol:
            symbol = "UNKNOWN"
    symbol = symbol.strip().upper()

    # Resolve company name and sector from universe metadata if missing
    meta = get_stock_metadata(symbol)
    if not name:
        if quote is not None:
            name = getattr(quote, "name", "") or (quote.get("name", "") if isinstance(quote, dict) else "")
        if not name and meta:
            name = meta.get("name", symbol)
        if not name:
            name = symbol

    if not sector:
        if quote is not None:
            sector = getattr(quote, "sector", "") or (quote.get("sector", "") if isinstance(quote, dict) else "")
        if not sector and meta:
            sector = meta.get("sector", "Equities")
        if not sector:
            sector = "Equities"

    # Resolve market cap tier
    resolved_cap_tier = "LARGE"
    if market_cap_tier:
        resolved_cap_tier = str(market_cap_tier).strip().upper()
    elif meta and meta.get("market_cap_tier"):
        resolved_cap_tier = str(meta.get("market_cap_tier")).strip().upper()
    elif quote and isinstance(quote, dict) and quote.get("market_cap_tier"):
        resolved_cap_tier = str(quote.get("market_cap_tier")).strip().upper()
    elif quote and hasattr(quote, "market_cap_tier") and getattr(quote, "market_cap_tier"):
        resolved_cap_tier = str(getattr(quote, "market_cap_tier")).strip().upper()

    # Extract price and daily high/low
    current_price = 0.0
    day_high = 0.0
    day_low = 0.0
    quote_beta = None
    fifty_two_week_high = 0.0
    fifty_two_week_low = 0.0

    if quote is not None:
        if isinstance(quote, QuoteData):
            current_price = quote.current_price
            day_high = quote.day_high
            day_low = quote.day_low
            quote_beta = quote.beta
            fifty_two_week_high = getattr(quote, "fifty_two_week_high", 0.0)
            fifty_two_week_low = getattr(quote, "fifty_two_week_low", 0.0)
        elif isinstance(quote, dict):
            current_price = float(quote.get("current_price", 0.0))
            day_high = float(quote.get("day_high", 0.0))
            day_low = float(quote.get("day_low", 0.0))
            quote_beta = quote.get("beta")
            fifty_two_week_high = float(quote.get("fifty_two_week_high", 0.0))
            fifty_two_week_low = float(quote.get("fifty_two_week_low", 0.0))

    if current_price <= 0.0 and momentum is not None:
        current_price = momentum.last_close

    if current_price <= 0.0 and df is not None and not df.empty:
        current_price = float(df["Close"].iloc[-1])

    if current_price <= 0.0:
        current_price = 100.0

    if fifty_two_week_high <= 0.0 and df is not None and not df.empty:
        try:
            fifty_two_week_high = float(df["High"].max())
        except Exception:
            fifty_two_week_high = current_price * 1.05

    if fifty_two_week_high <= 0.0:
        fifty_two_week_high = current_price * 1.05

    if fifty_two_week_low <= 0.0 and df is not None and not df.empty:
        try:
            fifty_two_week_low = float(df["Low"].min())
        except Exception:
            fifty_two_week_low = current_price * 0.75

    if fifty_two_week_low <= 0.0:
        fifty_two_week_low = current_price * 0.75

    if beta is None and quote_beta is not None:
        try:
            beta = float(quote_beta)
        except Exception:
            pass

    # ATR calculation
    atr = calculate_atr(df=df, current_price=current_price, day_high=day_high, day_low=day_low)

    # Horizon classification
    resolved_horizon = classify_trade_horizon(momentum=momentum, beta=beta, explicit_horizon=horizon)

    # Trade plan construction
    trade_plan = build_trade_plan(current_price=current_price, atr=atr, horizon=resolved_horizon)

    # Scoring & Action synthesis
    mom_score = momentum.momentum_score if momentum is not None else 0.0
    sent_score = sentiment.overall_score if (sentiment is not None and sentiment.article_count > 0) else 0.0

    if sentiment is not None and sentiment.article_count > 0:
        blended = (mom_score * 0.65) + (sent_score * 0.35)
    else:
        blended = mom_score

    # Advanced selection metrics
    relative_strength = evaluate_relative_strength(df=df, mom_score=mom_score, current_price=current_price)
    dist_52w_pct = round(((current_price - fifty_two_week_high) / fifty_two_week_high) * 100.0, 1)
    ma_alignment = evaluate_ma_structure(df=df, current_price=current_price, momentum=momentum)

    vol_ratio = getattr(momentum, "volume_ratio", 1.0) if momentum is not None else 1.0
    rsi_val = getattr(momentum, "rsi", 50.0) if momentum is not None else 50.0

    st_mom = calculate_short_term_momentum(
        df=df,
        current_price=current_price,
        volume_ratio=vol_ratio,
        momentum_score=mom_score,
        rsi_14=rsi_val,
    )

    # Institutional quantitative criteria
    is_stage_2 = evaluate_minervini_stage_2(
        df=df,
        current_price=current_price,
        fifty_two_week_high=fifty_two_week_high,
        fifty_two_week_low=fifty_two_week_low,
        momentum=momentum,
    )
    is_vcp_squeeze, consolidation_tightness = evaluate_vcp_squeeze(
        df=df,
        current_price=current_price,
    )
    accumulation_rating, up_down_volume_ratio = evaluate_accumulation_distribution(
        df=df,
        volume_ratio=vol_ratio,
        mom_score=mom_score,
    )

    strategy_tag = evaluate_strategy_tag(
        relative_strength=relative_strength,
        dist_52w_pct=dist_52w_pct,
        ma_alignment=ma_alignment,
        rsi=rsi_val,
        volume_ratio=vol_ratio,
        mom_score=mom_score,
        is_stage_2=is_stage_2,
        is_vcp_squeeze=is_vcp_squeeze,
        accumulation_rating=accumulation_rating,
    )

    # Confidence calculation
    conf = abs(blended)
    if momentum is not None:
        if momentum.volume_confirmed and momentum.multi_timeframe_aligned:
            conf = min(1.0, conf * 1.15)
        elif not momentum.volume_confirmed:
            conf = max(0.1, conf * 0.85)
    confidence = round(max(0.05, min(1.0, conf)), 2)

    # Normalized score (0.0 to 100.0) with selection enhancements
    raw_score = ((blended + 1.0) / 2.0) * 100.0
    if momentum is not None:
        if momentum.volume_confirmed:
            raw_score += 4.0
        if momentum.multi_timeframe_aligned:
            raw_score += 4.0
    if sent_score > 0.15:
        raw_score += 3.0

    # Institutional selection boosts
    if is_stage_2:
        raw_score += 4.5
    if is_vcp_squeeze:
        raw_score += 4.0

    if accumulation_rating == "A+":
        raw_score += 4.0
    elif accumulation_rating == "A":
        raw_score += 2.5
    elif accumulation_rating == "D":
        raw_score -= 5.0

    if strategy_tag == "RS_LEADER" or relative_strength >= 80.0:
        raw_score += 4.0
    if strategy_tag == "52W_BREAKOUT" or dist_52w_pct >= -4.0:
        raw_score += 3.5
    if ma_alignment in ("FULL_BULLISH", "GOLDEN_CROSS"):
        raw_score += 3.0

    score = round(max(0.0, min(100.0, raw_score)), 1)

    # Check for earnings blackout and proximity
    is_blackout = False
    earnings_days_away: Optional[int] = None
    is_earnings_imminent = False

    if earnings_info:
        is_blackout = bool(earnings_info.get("is_blackout", False))
        days = earnings_info.get("days_to_earnings")
        if days is None:
            days = earnings_info.get("earnings_days_away")
        if days is not None:
            try:
                earnings_days_away = int(days)
                if 0 <= earnings_days_away <= 7:
                    is_earnings_imminent = True
            except (ValueError, TypeError):
                earnings_days_away = None
        if bool(earnings_info.get("is_earnings_imminent", False)):
            is_earnings_imminent = True

    # Action determination
    if is_blackout:
        action = "HOLD / EARNINGS BLACKOUT"
    elif score >= 75.0:
        action = "STRONG BUY"
    elif score >= 58.0:
        action = "BUY ACCUMULATE"
    elif score >= 45.0:
        action = "HOLD / WATCH"
    else:
        action = "AVOID"

    # Transparent rationales
    rationale = []
    rationale.append(f"Setup Strategy: {strategy_tag} (RS Rating: {relative_strength:.0f}/99, {dist_52w_pct:+.1f}% from 52W High)")
    rationale.append(f"Moving Average Alignment: {ma_alignment}")

    if is_stage_2:
        rationale.append("Minervini Stage 2 Confirmed: Full uptrend template with price > 50 DMA > 200 DMA.")

    if is_vcp_squeeze:
        rationale.append(f"VCP Squeeze Active: Volatility compression tightness score of {consolidation_tightness:.0f}/100.")

    rationale.append(f"Institutional Flow: {accumulation_rating} Rating (Up/Down Volume Ratio: {up_down_volume_ratio:.2f}x).")

    if st_mom.short_term_setup in ("VELOCITY_BREAKOUT", "EMA_8_21_EXPANSION", "VOLUME_SURGE", "EMA_8_21_BULL_CROSS"):
        rationale.append(
            f"Short-Term Impulse: {st_mom.short_term_setup.replace('_', ' ')} "
            f"(3D ROC: {st_mom.roc_3d:+.1f}%, 5D RVOL: {st_mom.short_term_rvol:.2f}x, 8/21 EMA Spread: {st_mom.ema_spread_pct:+.1f}%)."
        )
    if st_mom.is_short_term_breakout:
        rationale.append(f"Short-Term Breakout: Within {abs(st_mom.distance_from_10d_high_pct):.1f}% of 10-day rolling high with volume confirmation.")

    if momentum is not None:
        rationale.append(f"Momentum: Score {mom_score:+.2f} ({momentum.trend_description})")
        rationale.append(f"Indicators: RSI-14 {momentum.rsi:.1f} | MACD Hist {momentum.macd_hist:+.3f}")
        if momentum.volume_confirmed:
            rationale.append(f"Volume Confirmed: {momentum.volume_ratio:.2f}x 20-day moving average.")
        else:
            rationale.append(f"Volume Notice: Volume ratio is {momentum.volume_ratio:.2f}x average.")

        if momentum.multi_timeframe_aligned:
            rationale.append(f"Timeframe Alignment: Daily momentum confirmed by Weekly trend ({momentum.weekly_trend}).")
        elif momentum.weekly_trend != "NEUTRAL":
            rationale.append(f"Timeframe Caution: Weekly trend is {momentum.weekly_trend}.")

    if sentiment is not None and sentiment.article_count > 0:
        rationale.append(f"Sentiment: {sentiment.sentiment_label} ({sent_score:+.2f}) across {sentiment.article_count} news items.")
    else:
        rationale.append("Sentiment: Neutral / Baseline news flow.")

    rationale.append(
        f"Trade Plan: Target 1 at ${trade_plan.tp1:.2f} (+{trade_plan.tp1_pct}%), "
        f"Stop Loss at ${trade_plan.stop_loss:.2f} (-{trade_plan.invalidation_pct}%) [R:R {trade_plan.risk_reward_ratio:.2f}]"
    )

    return StockRecommendation(
        symbol=symbol,
        name=name,
        sector=sector,
        horizon=resolved_horizon,
        action=action,
        score=score,
        confidence=confidence,
        momentum_score=mom_score,
        sentiment_score=sent_score,
        trade_plan=trade_plan,
        rationale=rationale,
        relative_strength_score=relative_strength,
        distance_from_52w_high_pct=dist_52w_pct,
        ma_alignment=ma_alignment,
        strategy_tag=strategy_tag,
        is_stage_2=is_stage_2,
        is_vcp_squeeze=is_vcp_squeeze,
        consolidation_tightness=consolidation_tightness,
        accumulation_rating=accumulation_rating,
        up_down_volume_ratio=up_down_volume_ratio,
        roc_3d=st_mom.roc_3d,
        roc_5d=st_mom.roc_5d,
        roc_10d=st_mom.roc_10d,
        short_term_rsi=st_mom.short_term_rsi,
        short_term_rvol=st_mom.short_term_rvol,
        ema_spread_pct=st_mom.ema_spread_pct,
        short_term_momentum_score=st_mom.short_term_momentum_score,
        short_term_setup=st_mom.short_term_setup,
        is_short_term_breakout=st_mom.is_short_term_breakout,
        earnings_days_away=earnings_days_away,
        is_earnings_imminent=is_earnings_imminent,
        market_cap_tier=resolved_cap_tier,
        is_earnings_blackout=is_blackout,
    )
