"""Tests for stock screener backend multi-filters and earnings proximity enhancements."""

import pytest
from fastapi.testclient import TestClient

from analysis.screener_cache import StockScreenerCache
from analysis.stock_suggester import (
    StockRecommendation,
    generate_stock_recommendation,
)
from api import app


def test_screener_cache_strategy_preset_filtering():
    """Verify strategy_preset='STAGE_2_LEADERS' returns only stage 2 stocks."""
    cache = StockScreenerCache(seed_defaults=True)
    res = cache.get_recommendations(strategy_preset="STAGE_2_LEADERS")

    assert "items" in res
    items = res["items"]
    assert len(items) > 0

    for item in items:
        is_stage_2 = item.get("is_stage_2", False)
        tag = item.get("strategy_tag", "")
        assert is_stage_2 or tag in ("STAGE_2_LEADER", "STAGE_2_LEADERS")

    # Verify non-stage 2 items from seeds (e.g. FCX, AMD) are excluded
    symbols = [it["symbol"] for it in items]
    assert "FCX" not in symbols
    assert "AMD" not in symbols


def test_screener_cache_price_range_filtering():
    """Verify min_price=50 and max_price=150 filter correctly."""
    cache = StockScreenerCache(seed_defaults=True)
    res = cache.get_recommendations(min_price=50.0, max_price=150.0)

    assert "items" in res
    items = res["items"]
    assert len(items) > 0

    for item in items:
        price = item.get("price") or item.get("trade_plan", {}).get("current_price", 0.0)
        assert 50.0 <= price <= 150.0

    symbols = [it["symbol"] for it in items]
    # PLTR is ~43.75 (< 50) -> excluded
    assert "PLTR" not in symbols
    # TSLA is ~260.50 (> 150) -> excluded
    assert "TSLA" not in symbols
    # NVDA is ~141.20 -> included
    assert "NVDA" in symbols


def test_screener_cache_min_rr_filtering():
    """Verify min_rr=2.0 filters items with risk_reward_ratio >= 2.0."""
    cache = StockScreenerCache(seed_defaults=True)
    res = cache.get_recommendations(min_rr=2.0)

    assert "items" in res
    items = res["items"]
    assert len(items) > 0

    for item in items:
        rr = float(item.get("risk_reward_ratio") or item.get("trade_plan", {}).get("risk_reward_ratio", 0.0))
        assert rr >= 2.0

    symbols = [it["symbol"] for it in items]
    # AAPL has R:R 1.95 (< 2.0) -> excluded
    assert "AAPL" not in symbols
    # AMD has R:R 1.92 (< 2.0) -> excluded
    assert "AMD" not in symbols
    # NVDA has R:R 2.15 (>= 2.0) -> included
    assert "NVDA" in symbols


def test_screener_cache_earnings_proximity_flag():
    """Verify stocks with upcoming earnings include earnings_days_away and is_earnings_imminent."""
    # 1. Imminent earnings (within 7 days)
    rec_imminent = generate_stock_recommendation(
        symbol="AAPL",
        quote={"current_price": 230.0, "valid": True},
        earnings_info={"days_to_earnings": 4, "is_blackout": True},
    )
    assert rec_imminent.earnings_days_away == 4
    assert rec_imminent.is_earnings_imminent is True
    assert rec_imminent.market_cap_tier in ("MEGA", "LARGE")

    # 2. Distant earnings (> 7 days)
    rec_distant = generate_stock_recommendation(
        symbol="NVDA",
        quote={"current_price": 140.0, "valid": True},
        earnings_info={"days_to_earnings": 28, "is_blackout": False},
    )
    assert rec_distant.earnings_days_away == 28
    assert rec_distant.is_earnings_imminent is False
    assert rec_distant.market_cap_tier in ("MEGA", "LARGE")

    # 3. Screener cache exclude_earnings_blackout filtering
    cache = StockScreenerCache()
    cache._set_cached_items([rec_imminent, rec_distant])

    # Unfiltered should contain both
    res_all = cache.get_recommendations()
    assert len(res_all["items"]) == 2

    # Filtered by exclude_earnings_blackout
    res_filtered = cache.get_recommendations(exclude_earnings_blackout=True)
    filtered_symbols = [it["symbol"] for it in res_filtered["items"]]
    assert "AAPL" not in filtered_symbols
    assert "NVDA" in filtered_symbols


def test_api_stocks_recommendations_filters():
    """Verify FastAPI GET /api/stocks/recommendations passes through query parameters."""
    client = TestClient(app)
    resp = client.get(
        "/api/stocks/recommendations",
        params={
            "strategy_preset": "STAGE_2_LEADERS",
            "min_price": 50.0,
            "max_price": 150.0,
            "min_rr": 2.0,
            "exclude_earnings_blackout": "true",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    for item in data["items"]:
        price = item.get("price") or item.get("trade_plan", {}).get("current_price", 0.0)
        assert 50.0 <= price <= 150.0
        rr = float(item.get("risk_reward_ratio") or item.get("trade_plan", {}).get("risk_reward_ratio", 0.0))
        assert rr >= 2.0
