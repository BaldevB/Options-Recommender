"""Technical momentum analysis with volume confirmation and multi-timeframe alignment.

Calculates RSI, MACD, Moving Averages (SMA20/SMA50), Volume Ratio, and
checks weekly trend alignment to ensure strong momentum is confirmed across timeframes.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import numpy as np
import pandas as pd
from config import TechnicalConfig, DEFAULT_CONFIG


@dataclass
class MomentumResult:
    """Structured technical momentum indicators, confirmations, and score."""
    symbol: str
    last_close: float
    rsi: float
    macd_line: float
    macd_signal: float
    macd_hist: float
    sma_short: float
    sma_long: float
    volume_ratio: float
    volume_confirmed: bool
    weekly_trend: str              # "BULLISH", "BEARISH", "NEUTRAL"
    multi_timeframe_aligned: bool
    trend_description: str
    momentum_score: float          # -1.0 (strong bear) to +1.0 (strong bull)
    details: Dict[str, Any]


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index (RSI) using exponential smoothing."""
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)

    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(50.0)


def calculate_macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> Dict[str, pd.Series]:
    """Calculate MACD Line, Signal Line, and Histogram."""
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    macd_signal = macd_line.ewm(span=signal, adjust=False).mean()
    macd_hist = macd_line - macd_signal

    return {
        "macd": macd_line,
        "signal": macd_signal,
        "hist": macd_hist,
    }


def check_weekly_timeframe(df: pd.DataFrame) -> Dict[str, Any]:
    """Resample daily history to weekly bars to assess intermediate trend alignment."""
    result = {"weekly_trend": "NEUTRAL", "weekly_close": 0.0, "weekly_sma10": 0.0}
    try:
        weekly = df.resample("W").agg({
            "Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"
        }).dropna()

        if len(weekly) >= 10:
            weekly_close = float(weekly["Close"].iloc[-1])
            weekly_sma10 = float(weekly["Close"].rolling(10).mean().iloc[-1])
            result["weekly_close"] = round(weekly_close, 2)
            result["weekly_sma10"] = round(weekly_sma10, 2)

            if weekly_close > weekly_sma10 * 1.01:
                result["weekly_trend"] = "BULLISH"
            elif weekly_close < weekly_sma10 * 0.99:
                result["weekly_trend"] = "BEARISH"
            else:
                result["weekly_trend"] = "NEUTRAL"
    except Exception:
        pass
    return result


def analyze_momentum(
    df: pd.DataFrame,
    symbol: str = "TICKER",
    cfg: Optional[TechnicalConfig] = None
) -> Optional[MomentumResult]:
    """Compute technical momentum metrics with volume and multi-timeframe confirmation.

    Args:
        df: Price history dataframe with ['Open', 'High', 'Low', 'Close', 'Volume']
        symbol: Ticker symbol
        cfg: TechnicalConfig instance

    Returns:
        MomentumResult or None if insufficient data
    """
    if df is None or len(df) < 30:
        return None

    cfg = cfg or DEFAULT_CONFIG.technicals
    close = df["Close"]
    volume = df["Volume"]

    # Calculate indicators
    rsi_series = calculate_rsi(close, period=cfg.rsi_period)
    macd_dict = calculate_macd(close, fast=cfg.macd_fast, slow=cfg.macd_slow, signal=cfg.macd_signal)
    sma_short_series = close.rolling(window=cfg.sma_short).mean()
    sma_long_series = close.rolling(window=cfg.sma_long).mean()
    vol_ma_series = volume.rolling(window=cfg.volume_ma_period).mean()

    # Current snapshot
    last_close = float(close.iloc[-1])
    current_rsi = float(rsi_series.iloc[-1])
    current_macd = float(macd_dict["macd"].iloc[-1])
    current_signal = float(macd_dict["signal"].iloc[-1])
    current_hist = float(macd_dict["hist"].iloc[-1])
    prev_hist = float(macd_dict["hist"].iloc[-2]) if len(macd_dict["hist"]) > 1 else current_hist

    current_sma_short = float(sma_short_series.iloc[-1]) if not pd.isna(sma_short_series.iloc[-1]) else last_close
    current_sma_long = float(sma_long_series.iloc[-1]) if not pd.isna(sma_long_series.iloc[-1]) else last_close

    vol_ma = float(vol_ma_series.iloc[-1]) if not pd.isna(vol_ma_series.iloc[-1]) and vol_ma_series.iloc[-1] > 0 else 1.0
    current_vol = float(volume.iloc[-1])
    vol_ratio = float(current_vol / vol_ma) if vol_ma > 0 else 1.0

    # Volume Confirmation check
    volume_confirmed = vol_ratio >= cfg.volume_confirmation_threshold

    # Multi-timeframe weekly check
    weekly_info = check_weekly_timeframe(df)
    weekly_trend = weekly_info["weekly_trend"]

    # 1. RSI Score (-1.0 to +1.0)
    rsi_score = (current_rsi - 50.0) / 50.0
    rsi_score = max(-1.0, min(1.0, rsi_score))

    # 2. MACD Score (-1.0 to +1.0)
    macd_score = 0.0
    if current_hist > 0:
        macd_score += 0.5
        if current_hist >= prev_hist:
            macd_score += 0.5
    elif current_hist < 0:
        macd_score -= 0.5
        if current_hist <= prev_hist:
            macd_score -= 0.5

    # 3. Moving Average Score (-1.0 to +1.0)
    ma_score = 0.0
    if last_close > current_sma_short:
        ma_score += 0.4
    else:
        ma_score -= 0.4

    if last_close > current_sma_long:
        ma_score += 0.3
    else:
        ma_score -= 0.3

    if current_sma_short >= current_sma_long:
        ma_score += 0.3
    else:
        ma_score -= 0.3

    ma_score = max(-1.0, min(1.0, ma_score))

    # Raw blended momentum score
    raw_momentum = (rsi_score * 0.35) + (macd_score * 0.35) + (ma_score * 0.30)

    # Multi-timeframe confirmation factor
    multi_timeframe_aligned = False
    if raw_momentum > 0.15 and weekly_trend == "BULLISH":
        multi_timeframe_aligned = True
        raw_momentum *= 1.15
    elif raw_momentum < -0.15 and weekly_trend == "BEARISH":
        multi_timeframe_aligned = True
        raw_momentum *= 1.15
    elif (raw_momentum > 0.20 and weekly_trend == "BEARISH") or (raw_momentum < -0.20 and weekly_trend == "BULLISH"):
        # Counter-trend divergence penalty
        raw_momentum *= 0.75

    # Volume Confirmation Rule:
    # Require volume confirmation before treating momentum as "strong".
    # If volume is below average (< 1.0x), dampen raw momentum to prevent false breakouts.
    if not volume_confirmed and abs(raw_momentum) > 0.35:
        raw_momentum *= 0.70  # Dampen unconfirmed spikes
    elif volume_confirmed and vol_ratio >= 1.3:
        raw_momentum *= 1.10  # Volume surge bonus

    momentum_score = round(max(-1.0, min(1.0, raw_momentum)), 3)

    # Descriptive summary
    if momentum_score >= 0.40 and volume_confirmed:
        trend_desc = "Strong Bullish (Volume Confirmed)"
    elif momentum_score >= 0.30 and not volume_confirmed:
        trend_desc = "Moderate Bullish (Unconfirmed Volume)"
    elif momentum_score >= 0.15:
        trend_desc = "Moderate Bullish Momentum"
    elif momentum_score <= -0.40 and volume_confirmed:
        trend_desc = "Strong Bearish (Volume Confirmed)"
    elif momentum_score <= -0.30 and not volume_confirmed:
        trend_desc = "Moderate Bearish (Unconfirmed Volume)"
    elif momentum_score <= -0.15:
        trend_desc = "Moderate Bearish Momentum"
    else:
        trend_desc = "Neutral / Consolidating"

    return MomentumResult(
        symbol=symbol,
        last_close=round(last_close, 2),
        rsi=round(current_rsi, 1),
        macd_line=round(current_macd, 3),
        macd_signal=round(current_signal, 3),
        macd_hist=round(current_hist, 3),
        sma_short=round(current_sma_short, 2),
        sma_long=round(current_sma_long, 2),
        volume_ratio=round(vol_ratio, 2),
        volume_confirmed=volume_confirmed,
        weekly_trend=weekly_trend,
        multi_timeframe_aligned=multi_timeframe_aligned,
        trend_description=trend_desc,
        momentum_score=momentum_score,
        details={
            "rsi_score": round(rsi_score, 3),
            "macd_score": round(macd_score, 3),
            "ma_score": round(ma_score, 3),
            "above_sma20": last_close > current_sma_short,
            "above_sma50": last_close > current_sma_long,
            "sma20_above_sma50": current_sma_short >= current_sma_long,
            "weekly_sma10": weekly_info["weekly_sma10"],
        }
    )



@dataclass
class ShortTermMomentumResult:
    """Short-term momentum metrics specifically designed for 1-10 day swing and breakout selection."""
    roc_3d: float                      # 3-Day Rate of Change (%)
    roc_5d: float                      # 5-Day Rate of Change (%)
    roc_10d: float                     # 10-Day Rate of Change (%)
    short_term_rsi: float              # 5-period fast RSI
    short_term_rvol: float             # 5-Day Relative Volume Ratio (RVOL)
    ema_8: float                       # 8-period Exponential Moving Average
    ema_21: float                      # 21-period Exponential Moving Average
    ema_spread_pct: float              # ((EMA8 - EMA21) / EMA21) * 100
    ema_alignment: str                 # "BULLISH_EXPANSION", "BULL_CROSS", "BEARISH_EXPANSION", "BEAR_CROSS", "NEUTRAL"
    distance_from_10d_high_pct: float  # Proximity to 10-day high (0.0% = at high)
    distance_from_20d_high_pct: float  # Proximity to 20-day high (0.0% = at high)
    is_short_term_breakout: bool       # Price within 1.0% of 10-day high with RVOL >= 1.2
    short_term_momentum_score: float   # 0 to 100 composite score tailored for short-term selection
    short_term_setup: str              # "VELOCITY_BREAKOUT", "EMA_8_21_EXPANSION", "PULLBACK_BOUNCE", "VOLUME_SURGE", "MOMENTUM_CONSOLIDATION"
    details: Dict[str, Any]


def calculate_short_term_momentum(
    df: Optional[pd.DataFrame] = None,
    current_price: float = 100.0,
    volume_ratio: float = 1.0,
    momentum_score: float = 0.0,
    rsi_14: float = 50.0,
) -> ShortTermMomentumResult:
    """Calculate dedicated short-term momentum metrics for high-velocity stock selection.

    Evaluates:
    - 3-day, 5-day, and 10-day price velocity (Rate of Change / ROC)
    - 5-period fast RSI impulse
    - 5-day short-term relative volume (RVOL)
    - 8 EMA vs 21 EMA ribbon spread and crossover alignment
    - 10-day and 20-day breakout proximity
    - Normalized 0-100 short-term momentum composite score
    """
    price = max(0.01, current_price)
    roc_3d = 0.0
    roc_5d = 0.0
    roc_10d = 0.0
    short_term_rsi = rsi_14
    short_term_rvol = volume_ratio
    ema_8 = price
    ema_21 = price
    ema_spread_pct = 0.0
    ema_alignment = "NEUTRAL"
    dist_10d_high = 0.0
    dist_20d_high = 0.0

    if df is not None and not df.empty and len(df) >= 5:
        try:
            close = df["Close"]
            cur_close = float(close.iloc[-1])
            price = cur_close

            # 1. Price Velocity (ROC)
            if len(close) >= 4:
                p_3d_ago = float(close.iloc[-4])
                if p_3d_ago > 0:
                    roc_3d = ((cur_close - p_3d_ago) / p_3d_ago) * 100.0

            if len(close) >= 6:
                p_5d_ago = float(close.iloc[-6])
                if p_5d_ago > 0:
                    roc_5d = ((cur_close - p_5d_ago) / p_5d_ago) * 100.0

            if len(close) >= 11:
                p_10d_ago = float(close.iloc[-11])
                if p_10d_ago > 0:
                    roc_10d = ((cur_close - p_10d_ago) / p_10d_ago) * 100.0
            else:
                roc_10d = roc_5d * 1.5

            # 2. Fast 5-period RSI
            if len(close) >= 6:
                short_term_rsi = float(calculate_rsi(close, period=5).iloc[-1])

            # 3. 5-day RVOL
            if "Volume" in df.columns:
                vol = df["Volume"]
                cur_vol = float(vol.iloc[-1])
                w_5 = min(len(vol), 5)
                vol_5d_mean = float(vol.iloc[-w_5:].mean())
                if vol_5d_mean > 0:
                    short_term_rvol = cur_vol / vol_5d_mean

            # 4. 8 EMA vs 21 EMA Ribbon
            ema_8_series = close.ewm(span=8, adjust=False).mean()
            ema_21_series = close.ewm(span=21, adjust=False).mean()

            ema_8 = float(ema_8_series.iloc[-1])
            ema_21 = float(ema_21_series.iloc[-1])

            if ema_21 > 0:
                ema_spread_pct = ((ema_8 - ema_21) / ema_21) * 100.0

            if len(ema_8_series) >= 2 and len(ema_21_series) >= 2:
                prev_ema_8 = float(ema_8_series.iloc[-2])
                prev_ema_21 = float(ema_21_series.iloc[-2])

                if ema_8 > ema_21:
                    if prev_ema_8 <= prev_ema_21:
                        ema_alignment = "BULL_CROSS"
                    else:
                        ema_alignment = "BULLISH_EXPANSION"
                elif ema_8 < ema_21:
                    if prev_ema_8 >= prev_ema_21:
                        ema_alignment = "BEAR_CROSS"
                    else:
                        ema_alignment = "BEARISH_EXPANSION"
                else:
                    ema_alignment = "NEUTRAL"
            else:
                ema_alignment = "BULLISH_EXPANSION" if ema_8 >= ema_21 else "BEARISH_EXPANSION"

            # 5. Breakout Proximity (10-day & 20-day high)
            high = df["High"]
            w_10 = min(len(high), 10)
            high_10d = float(high.iloc[-w_10:].max())
            if high_10d > 0:
                dist_10d_high = ((cur_close - high_10d) / high_10d) * 100.0

            w_20 = min(len(high), 20)
            high_20d = float(high.iloc[-w_20:].max())
            if high_20d > 0:
                dist_20d_high = ((cur_close - high_20d) / high_20d) * 100.0

        except Exception:
            pass
    else:
        # Fallback estimation using general momentum inputs
        roc_3d = momentum_score * 4.0
        roc_5d = momentum_score * 6.0
        roc_10d = momentum_score * 8.5
        short_term_rsi = rsi_14
        short_term_rvol = volume_ratio
        ema_spread_pct = momentum_score * 3.0
        ema_8 = price * (1.0 + (momentum_score * 0.015))
        ema_21 = price * (1.0 - (momentum_score * 0.015))
        ema_alignment = "BULLISH_EXPANSION" if momentum_score > 0.15 else "NEUTRAL"
        dist_10d_high = -1.5 if momentum_score > 0.3 else -4.0
        dist_20d_high = -2.5 if momentum_score > 0.3 else -6.0

    # Short-Term Breakout Detection
    is_short_term_breakout = bool(dist_10d_high >= -1.0 and (short_term_rvol >= 1.20 or volume_ratio >= 1.20))

    # Composite Short-Term Momentum Score (0 to 100)
    score_acc = 50.0
    # Velocity contribution (+- 15 pts)
    score_acc += max(-15.0, min(15.0, roc_3d * 2.2))
    score_acc += max(-10.0, min(10.0, roc_5d * 1.2))

    # EMA Ribbon Spread (+- 12 pts)
    score_acc += max(-12.0, min(12.0, ema_spread_pct * 3.5))

    # Short-Term Volume Surge (+- 12 pts)
    if short_term_rvol >= 1.5:
        score_acc += 10.0
    elif short_term_rvol >= 1.2:
        score_acc += 5.0
    elif short_term_rvol < 0.8:
        score_acc -= 6.0

    # Fast RSI alignment (Sweet spot 55-75 = strong momentum impulse)
    if 55.0 <= short_term_rsi <= 75.0:
        score_acc += 8.0
    elif short_term_rsi > 75.0:
        score_acc += 4.0  # Slightly overbought but still high velocity
    elif short_term_rsi < 35.0:
        score_acc -= 7.0

    # Breakout bonus
    if is_short_term_breakout:
        score_acc += 8.0
    elif dist_10d_high >= -2.0:
        score_acc += 4.0

    short_term_score = round(max(5.0, min(99.0, score_acc)), 1)

    # Classify Short-Term Setup
    if is_short_term_breakout and roc_3d >= 2.5 and short_term_rvol >= 1.25:
        short_term_setup = "VELOCITY_BREAKOUT"
    elif ema_alignment == "BULL_CROSS":
        short_term_setup = "EMA_8_21_BULL_CROSS"
    elif ema_alignment == "BULLISH_EXPANSION" and ema_spread_pct >= 1.2:
        short_term_setup = "EMA_8_21_EXPANSION"
    elif short_term_rvol >= 1.50 and roc_3d >= 1.0:
        short_term_setup = "VOLUME_SURGE"
    elif short_term_rsi <= 44.0 and ema_8 >= ema_21 * 0.98:
        short_term_setup = "PULLBACK_BOUNCE"
    else:
        short_term_setup = "MOMENTUM_CONSOLIDATION"

    return ShortTermMomentumResult(
        roc_3d=round(roc_3d, 2),
        roc_5d=round(roc_5d, 2),
        roc_10d=round(roc_10d, 2),
        short_term_rsi=round(short_term_rsi, 1),
        short_term_rvol=round(short_term_rvol, 2),
        ema_8=round(ema_8, 2),
        ema_21=round(ema_21, 2),
        ema_spread_pct=round(ema_spread_pct, 2),
        ema_alignment=ema_alignment,
        distance_from_10d_high_pct=round(dist_10d_high, 1),
        distance_from_20d_high_pct=round(dist_20d_high, 1),
        is_short_term_breakout=is_short_term_breakout,
        short_term_momentum_score=short_term_score,
        short_term_setup=short_term_setup,
        details={
            "dist_10d_high": round(dist_10d_high, 1),
            "dist_20d_high": round(dist_20d_high, 1),
            "ema_8": round(ema_8, 2),
            "ema_21": round(ema_21, 2),
        }
    )
