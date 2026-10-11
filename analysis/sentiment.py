"""News sentiment analysis using local VADER with explicit recency decay weighting."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
from typing import List, Dict, Any
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class SentimentResult:
    """Structured sentiment scores and processed headline breakdown."""
    symbol: str
    overall_score: float  # -1.0 (very negative) to +1.0 (very positive)
    sentiment_label: str  # "Bullish", "Bearish", "Neutral"
    article_count: int
    positive_count: int
    negative_count: int
    neutral_count: int
    scored_articles: List[Dict[str, Any]] = field(default_factory=list)


# Singleton VADER analyzer instance
_ANALYZER = SentimentIntensityAnalyzer()


def analyze_headline(headline: str) -> Dict[str, float]:
    """Score a single headline using VADER."""
    if not headline or not headline.strip():
        return {"neg": 0.0, "neu": 1.0, "pos": 0.0, "compound": 0.0}
    return _ANALYZER.polarity_scores(headline)


def _compute_recency_weight(published_str: str, index: int) -> float:
    """Compute recency weight based on actual elapsed hours or list order.

    Fresh headlines within 6 hours receive full weight (1.0), decaying
    down over days.
    """
    now = datetime.now(timezone.utc)
    try:
        if published_str and published_str != "Recent":
            # Formats like "2026-10-06 17:33 UTC"
            clean_str = published_str.replace(" UTC", "")
            pub_dt = datetime.strptime(clean_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            hours_elapsed = (now - pub_dt).total_seconds() / 3600.0

            if hours_elapsed <= 6:
                return 1.00
            elif hours_elapsed <= 24:
                return 0.85
            elif hours_elapsed <= 48:
                return 0.65
            elif hours_elapsed <= 96:
                return 0.45
            else:
                return 0.25
    except Exception:
        pass

    # Fallback rank-based decay
    return round(1.0 / (1.0 + (0.12 * index)), 3)


def analyze_news_sentiment(
    articles: List[Dict[str, str]],
    symbol: str = "TICKER"
) -> SentimentResult:
    """Analyze news articles applying time-decay recency weights.

    Fresher news carries higher influence on the aggregate sentiment score.

    Args:
        articles: List of article dicts
        symbol: Ticker symbol

    Returns:
        SentimentResult
    """
    if not articles:
        return SentimentResult(
            symbol=symbol,
            overall_score=0.0,
            sentiment_label="Neutral (No News)",
            article_count=0,
            positive_count=0,
            negative_count=0,
            neutral_count=0,
            scored_articles=[]
        )

    scored_articles = []
    weighted_scores = []
    weights = []
    pos_cnt = 0
    neg_cnt = 0
    neu_cnt = 0

    for i, art in enumerate(articles):
        title = art.get("title", "")
        scores = analyze_headline(title)
        compound = scores["compound"]

        weight = _compute_recency_weight(art.get("published_at", ""), i)
        weights.append(weight)
        weighted_scores.append(compound * weight)

        if compound >= 0.05:
            pos_cnt += 1
            cat = "Positive"
        elif compound <= -0.05:
            neg_cnt += 1
            cat = "Negative"
        else:
            neu_cnt += 1
            cat = "Neutral"

        scored_articles.append({
            "title": title,
            "publisher": art.get("publisher", "Unknown"),
            "published_at": art.get("published_at", "Recent"),
            "link": art.get("link", ""),
            "compound": round(compound, 3),
            "weight": round(weight, 2),
            "category": cat,
        })

    total_weight = sum(weights) if weights else 1.0
    overall_score = sum(weighted_scores) / total_weight if total_weight > 0 else 0.0
    overall_score = round(max(-1.0, min(1.0, overall_score)), 3)

    if overall_score >= 0.15:
        sentiment_label = "Bullish Sentiment"
    elif overall_score <= -0.15:
        sentiment_label = "Bearish Sentiment"
    else:
        sentiment_label = "Neutral Sentiment"

    return SentimentResult(
        symbol=symbol,
        overall_score=overall_score,
        sentiment_label=sentiment_label,
        article_count=len(articles),
        positive_count=pos_cnt,
        negative_count=neg_cnt,
        neutral_count=neu_cnt,
        scored_articles=scored_articles
    )
