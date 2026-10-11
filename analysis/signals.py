"""Signal generation combining technical momentum, news sentiment, and earnings blackout checks."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from analysis.momentum import MomentumResult
from analysis.sentiment import SentimentResult
from config import SignalWeights, EarningsConfig, DEFAULT_CONFIG


class BiasDirection(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class ConfidenceTier(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class TradeSignal:
    """Comprehensive trading signal synthesized from momentum, sentiment, and earnings checks."""
    symbol: str
    bias: BiasDirection
    combined_score: float             # -1.0 to +1.0
    confidence: float                 # 0.0 to 1.0
    confidence_tier: ConfidenceTier   # HIGH / MEDIUM / LOW
    momentum_score: float
    sentiment_score: float
    is_earnings_blackout: bool
    earnings_info: Dict[str, Any] = field(default_factory=dict)
    rationale: List[str] = field(default_factory=list)
    action_suggestion: str = ""


def generate_signal(
    momentum: MomentumResult,
    sentiment: Optional[SentimentResult] = None,
    earnings_info: Optional[Dict[str, Any]] = None,
    weights: Optional[SignalWeights] = None,
    earnings_cfg: Optional[EarningsConfig] = None
) -> TradeSignal:
    """Combine momentum, sentiment, and earnings protection into a directional trade signal.

    Args:
        momentum: MomentumResult from analysis.momentum
        sentiment: SentimentResult from analysis.sentiment
        earnings_info: Dict from data.price_data.get_earnings_info
        weights: SignalWeights instance
        earnings_cfg: EarningsConfig instance

    Returns:
        TradeSignal dataclass with Confidence Tier and Blackout protection
    """
    weights = weights or DEFAULT_CONFIG.weights
    earnings_cfg = earnings_cfg or DEFAULT_CONFIG.earnings
    symbol = momentum.symbol

    mom_score = momentum.momentum_score
    sent_score = sentiment.overall_score if sentiment and sentiment.article_count > 0 else 0.0

    # Adjust weights dynamically if sentiment has no data
    if sentiment is None or sentiment.article_count == 0:
        eff_mom_weight = 1.0
        eff_sent_weight = 0.0
    else:
        eff_mom_weight = weights.momentum_weight
        eff_sent_weight = weights.sentiment_weight

    combined_score = (mom_score * eff_mom_weight) + (sent_score * eff_sent_weight)
    combined_score = round(max(-1.0, min(1.0, combined_score)), 3)

    # Base confidence is absolute combined score
    confidence = abs(combined_score)

    # Multi-factor alignment adjustments
    if momentum.volume_confirmed and momentum.multi_timeframe_aligned:
        confidence = min(1.0, confidence * 1.15)
    elif not momentum.volume_confirmed:
        confidence = max(0.0, confidence * 0.85)

    if (mom_score > 0.15 and sent_score < -0.15) or (mom_score < -0.15 and sent_score > 0.15):
        confidence = max(0.0, confidence * 0.70)

    confidence = round(confidence, 3)

    # Earnings Blackout Check
    earnings_info = earnings_info or {}
    is_blackout = bool(earnings_info.get("is_blackout", False))
    days_to_earnings = earnings_info.get("days_to_earnings")
    next_earnings_date = earnings_info.get("next_earnings_date")

    rationale = []

    # Directional Bias assignment
    if is_blackout:
        bias = BiasDirection.NEUTRAL
        confidence = min(confidence, 0.20)
        action = (
            f"⛔ EARNINGS BLACKOUT ACTIVE: Earnings reported in {days_to_earnings} days ({next_earnings_date}). "
            f"Avoid directional options due to binary announcement risk and IV crush."
        )
        rationale.append(f"Earnings blackout triggered: Expected in {days_to_earnings} days.")
    elif combined_score >= weights.medium_confidence_thresh:
        bias = BiasDirection.BULLISH
        action = "Look for liquid Call options (0.30-0.55 Delta, 14-45 DTE) or Bull Call Debit Spreads if IV is high."
    elif combined_score <= -weights.medium_confidence_thresh:
        bias = BiasDirection.BEARISH
        action = "Look for liquid Put options (0.30-0.55 Delta, 14-45 DTE) or Bear Put Debit Spreads if IV is high."
    else:
        bias = BiasDirection.NEUTRAL
        action = "Neutral / indecisive signals. No directional options trade recommended."

    # Determine Confidence Tier (High / Medium / Low)
    if is_blackout:
        confidence_tier = ConfidenceTier.LOW
    elif confidence >= weights.high_confidence_thresh and momentum.volume_confirmed:
        confidence_tier = ConfidenceTier.HIGH
    elif confidence >= weights.medium_confidence_thresh:
        confidence_tier = ConfidenceTier.MEDIUM
    else:
        confidence_tier = ConfidenceTier.LOW

    # Transparent rationale formulation
    rationale.append(f"Momentum Score: {mom_score:+.2f} ({momentum.trend_description})")
    rationale.append(f"RSI-14: {momentum.rsi:.1f} | MACD Hist: {momentum.macd_hist:+.3f}")

    if momentum.volume_confirmed:
        rationale.append(f"Volume Confirmed: Current volume is {momentum.volume_ratio:.2f}x of 20-day average.")
    else:
        rationale.append(f"Volume Caution: Below average volume ({momentum.volume_ratio:.2f}x); strong breakout unconfirmed.")

    if momentum.multi_timeframe_aligned:
        rationale.append(f"Multi-Timeframe: Daily momentum aligned with Weekly trend ({momentum.weekly_trend}).")
    elif momentum.weekly_trend != "NEUTRAL":
        rationale.append(f"Multi-Timeframe Divergence: Weekly trend is {momentum.weekly_trend} while short-term momentum is {bias.value}.")

    if sentiment and sentiment.article_count > 0:
        rationale.append(
            f"News Sentiment: {sent_score:+.2f} ({sentiment.sentiment_label}) across {sentiment.article_count} headlines "
            f"(recency-weighted)."
        )
    else:
        rationale.append("News Sentiment: Neutral (No recent headlines found).")

    if earnings_info.get("is_warning") and not is_blackout:
        rationale.append(f"Earnings Alert: Earnings scheduled in {days_to_earnings} days ({next_earnings_date}).")

    return TradeSignal(
        symbol=symbol,
        bias=bias,
        combined_score=combined_score,
        confidence=confidence,
        confidence_tier=confidence_tier,
        momentum_score=mom_score,
        sentiment_score=sent_score,
        is_earnings_blackout=is_blackout,
        earnings_info=earnings_info,
        rationale=rationale,
        action_suggestion=action,
    )
