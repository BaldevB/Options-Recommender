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
