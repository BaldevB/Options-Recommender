"""Quantitative stock trade recommendation engine.

Calculates actionable trade plans (Entry Zone, TP1, TP2, Stop Loss, Risk-Reward ratio),
classifies trade horizon (SWING vs LONG_TERM), evaluates overall composite score, and
determines risk-based integer share position sizing for 1,000+ US equities.
"""

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Tuple, List, Dict, Any, Optional, Union
import numpy as np
import pandas as pd

from analysis.momentum import MomentumResult
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
        # Low beta (< 1.15) with aligned weekly trend suggests steady investment
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
    **kwargs,
) -> StockRecommendation:
    """Generate a quantitative stock recommendation with actionable trade plan and scoring.

    Args:
        target: Optional primary argument (symbol, quote, or momentum).
        *args: Variable positional arguments for flexible invocation.
        symbol: Ticker symbol (e.g. 'NVDA').
        quote: QuoteData or quote dict.
        momentum: MomentumResult from analysis.momentum.
        sentiment: SentimentResult from analysis.sentiment.
        df: Price history dataframe for ATR calculation.
        beta: Volatility beta.
        sector: Sector category.
        name: Company name.
        horizon: Desired TradeHorizon (SWING / LONG_TERM).
        earnings_info: Earnings calendar info.

    Returns:
        StockRecommendation
    """
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

    # Extract price and daily high/low
    current_price = 0.0
    day_high = 0.0
    day_low = 0.0
    quote_beta = None

    if quote is not None:
        if isinstance(quote, QuoteData):
            current_price = quote.current_price
            day_high = quote.day_high
            day_low = quote.day_low
            quote_beta = quote.beta
        elif isinstance(quote, dict):
            current_price = float(quote.get("current_price", 0.0))
            day_high = float(quote.get("day_high", 0.0))
            day_low = float(quote.get("day_low", 0.0))
            quote_beta = quote.get("beta")

    if current_price <= 0.0 and momentum is not None:
        current_price = momentum.last_close

    if current_price <= 0.0 and df is not None and not df.empty:
        current_price = float(df["Close"].iloc[-1])

    if current_price <= 0.0:
        current_price = 100.0

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

    # Confidence calculation
    conf = abs(blended)
    if momentum is not None:
        if momentum.volume_confirmed and momentum.multi_timeframe_aligned:
            conf = min(1.0, conf * 1.15)
        elif not momentum.volume_confirmed:
            conf = max(0.1, conf * 0.85)
    confidence = round(max(0.05, min(1.0, conf)), 2)

    # Normalized score (0.0 to 100.0)
    raw_score = ((blended + 1.0) / 2.0) * 100.0
    if momentum is not None:
        if momentum.volume_confirmed:
            raw_score += 4.0
        if momentum.multi_timeframe_aligned:
            raw_score += 4.0
    if sent_score > 0.15:
        raw_score += 3.0
    score = round(max(0.0, min(100.0, raw_score)), 1)

    # Check for earnings blackout
    is_blackout = False
    if earnings_info:
        is_blackout = bool(earnings_info.get("is_blackout", False))

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
    )
