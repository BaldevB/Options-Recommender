"""News data fetching and extraction via yfinance search and ticker feeds."""

from datetime import datetime, timezone
import logging
from typing import List, Dict, Any
import yfinance as yf

logger = logging.getLogger(__name__)


def _extract_title(item: Dict[str, Any]) -> str:
    """Safely extract headline title across varying Yahoo news schemas."""
    # Direct top-level title
    if "title" in item and item["title"]:
        return str(item["title"]).strip()
    # Nested in content (Yahoo Finance 2024+ format)
    content = item.get("content")
    if isinstance(content, dict) and "title" in content and content["title"]:
        return str(content["title"]).strip()
    return ""


def _extract_publisher(item: Dict[str, Any]) -> str:
    """Safely extract publisher source name."""
    if "publisher" in item and item["publisher"]:
        return str(item["publisher"]).strip()
    content = item.get("content")
    if isinstance(content, dict):
        provider = content.get("provider")
        if isinstance(provider, dict) and "displayName" in provider:
            return str(provider["displayName"]).strip()
    return "Yahoo Finance"


def _extract_timestamp(item: Dict[str, Any]) -> str:
    """Extract and format publication time."""
    ts = item.get("providerPublishTime")
    if ts and isinstance(ts, (int, float)):
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        except Exception:
            pass
    return "Recent"


def _extract_link(item: Dict[str, Any]) -> str:
    """Safely extract article URL."""
    if "link" in item and item["link"]:
        return str(item["link"])
    content = item.get("content")
    if isinstance(content, dict):
        canonical_url = content.get("canonicalUrl")
        if isinstance(canonical_url, dict) and "url" in canonical_url:
            return str(canonical_url["url"])
        if "clickThroughUrl" in content and isinstance(content["clickThroughUrl"], dict):
            return str(content["clickThroughUrl"].get("url", ""))
    return ""


def get_company_news(symbol: str, limit: int = 10) -> List[Dict[str, str]]:
    """Retrieve recent news articles for a stock symbol.

    Uses yfinance Search and Ticker feeds to get current headlines.

    Args:
        symbol: Ticker symbol (e.g., 'NVDA', 'AAPL')
        limit: Maximum number of articles to return

    Returns:
        List of dicts: [{'title': str, 'publisher': str, 'link': str, 'published_at': str}]
    """
    symbol = symbol.strip().upper()
    articles: List[Dict[str, str]] = []
    seen_titles = set()

    # Strategy 1: yf.Search (most reliable in modern yfinance versions)
    try:
        search_obj = yf.Search(symbol, news_count=limit * 2)
        raw_news = getattr(search_obj, "news", []) or []
        for item in raw_news:
            if not isinstance(item, dict):
                continue
            title = _extract_title(item)
            if title and title.lower() not in seen_titles:
                seen_titles.add(title.lower())
                articles.append({
                    "title": title,
                    "publisher": _extract_publisher(item),
                    "link": _extract_link(item),
                    "published_at": _extract_timestamp(item),
                })
                if len(articles) >= limit:
                    break
    except Exception as exc:
        logger.warning("yf.Search news retrieval failed for %s: %s", symbol, exc)

    # Strategy 2: Fallback to ticker.news if search returned few results
    if len(articles) < limit:
        try:
            ticker = yf.Ticker(symbol)
            ticker_news = getattr(ticker, "news", []) or []
            for item in ticker_news:
                if not isinstance(item, dict):
                    continue
                title = _extract_title(item)
                if title and title.lower() not in seen_titles:
                    seen_titles.add(title.lower())
                    articles.append({
                        "title": title,
                        "publisher": _extract_publisher(item),
                        "link": _extract_link(item),
                        "published_at": _extract_timestamp(item),
                    })
                    if len(articles) >= limit:
                        break
        except Exception as exc:
            logger.warning("ticker.news fallback failed for %s: %s", symbol, exc)

    return articles
