"""Unit and Integration tests for FastAPI Stock Recommendations & Paper Trading Endpoints."""

from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from api import app, check_is_expired, parse_occ_symbol
from analysis.screener_cache import get_screener_cache
from analysis.stock_suggester import TradeHorizon, StockTradePlan, StockRecommendation


def _create_sample_rec(
    symbol: str = "NVDA",
    name: str = "NVIDIA Corporation",
    sector: str = "technology",
    score: float = 88.0,
    price: float = 120.0,
) -> StockRecommendation:
    plan = StockTradePlan(
        entry_zone=(price * 0.99, price * 1.01),
        current_price=price,
        tp1=round(price * 1.08, 2),
        tp2=round(price * 1.15, 2),
        stop_loss=round(price * 0.95, 2),
        risk_reward_ratio=1.6,
        invalidation_pct=5.0,
        tp1_pct=8.0,
        tp2_pct=15.0,
    )
    return StockRecommendation(
        symbol=symbol,
        name=name,
        sector=sector,
        horizon=TradeHorizon.SWING,
        action="STRONG BUY",
        score=score,
        confidence=0.88,
        momentum_score=0.55,
        sentiment_score=0.30,
        trade_plan=plan,
        rationale=[f"Strong breakout setup for {symbol}"],
    )


@pytest.fixture(autouse=True)
def seed_test_cache():
    """Seed singleton cache with predictable test items."""
    cache = get_screener_cache()
    rec1 = _create_sample_rec("NVDA", "NVIDIA Corporation", "technology", 88.0, 120.0)
    rec2 = _create_sample_rec("AAPL", "Apple Inc.", "technology", 79.0, 220.0)
    rec3 = _create_sample_rec("JNJ", "Johnson & Johnson", "healthcare", 65.0, 160.0)
    cache._set_cached_items([rec1, rec2, rec3])
    yield


def test_api_stocks_recommendations():
    """GET /api/stocks/recommendations returns 200 OK with list of results."""
    client = TestClient(app)
    resp = client.get("/api/stocks/recommendations")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 1
    symbols = [it["symbol"] for it in data["items"]]
    assert "NVDA" in symbols


def test_api_stocks_universe():
    """GET /api/stocks/universe returns list of sectors and catalog counts."""
    client = TestClient(app)
    resp = client.get("/api/stocks/universe")
    assert resp.status_code == 200
    data = resp.json()
    assert "sectors" in data
    assert isinstance(data["sectors"], (list, dict))
    assert len(data["sectors"]) > 0
    assert "total_stocks" in data
    assert data["total_stocks"] >= 1000


def test_api_stocks_analysis_symbol():
    """GET /api/stocks/analysis?symbol=NVDA returns trade plan and technical scores."""
    client = TestClient(app)
    resp = client.get("/api/stocks/analysis?symbol=NVDA")
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "NVDA"
    assert "trade_plan" in data
    assert "current_price" in data["trade_plan"]
    assert "tp1" in data["trade_plan"]
    assert "stop_loss" in data["trade_plan"]
    assert "risk_reward_ratio" in data["trade_plan"]


def test_api_stocks_analysis_not_found():
    """GET /api/stocks/analysis?symbol=UNKNOWN returns 404 when stock cannot be analyzed."""
    client = TestClient(app)
    with patch("analysis.screener_cache.fetch_single_stock_analysis", return_value=None):
        resp = client.get("/api/stocks/analysis?symbol=UNKNOWN_TICKER_XYZ")
        assert resp.status_code == 404


def test_api_stocks_status():
    """GET /api/stocks/status returns cache status and health metrics."""
    client = TestClient(app)
    resp = client.get("/api/stocks/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "cached_stocks" in data
    assert "total_stocks" in data
    assert data["cached_stocks"] >= 3


def test_api_stocks_refresh():
    """POST /api/stocks/refresh triggers cache refresh."""
    client = TestClient(app)
    with patch("analysis.screener_cache.StockScreenerCache.refresh_cache", return_value={"status": "success", "scanned_stocks": 5}):
        resp = client.post("/api/stocks/refresh", json={"force": True})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"


def test_api_stocks_filtering_and_pagination():
    """GET /api/stocks/recommendations respects sector, horizon, limit and offset."""
    client = TestClient(app)
    resp = client.get("/api/stocks/recommendations?sector=technology&limit=1&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["limit"] == 1
    assert data["offset"] == 0
    assert len(data["items"]) == 1
    assert data["items"][0]["sector"] == "technology"


def test_api_paper_quotes_with_stocks():
    """POST /api/paper-quotes supports both option contracts and plain stock symbols."""
    client = TestClient(app)

    mock_fast_nvda = MagicMock(last_price=125.50, previous_close=122.00)
    mock_fast_opt = MagicMock(last_price=4.50, previous_close=4.00)

    mock_ticker_nvda = MagicMock(fast_info=mock_fast_nvda)
    mock_ticker_opt = MagicMock(fast_info=mock_fast_opt)

    def get_ticker_mock(sym):
        if "NVDA26" in sym:
            return mock_ticker_opt
        return mock_ticker_nvda

    mock_tickers = MagicMock()
    mock_tickers.tickers.get.side_effect = get_ticker_mock

    future_contract = "NVDA261218C00230000"  # Expiring Dec 2026 (active)
    payload = {
        "items": [
            {"symbol": "NVDA", "asset_type": "STOCK"},
            {"contract": future_contract, "asset_type": "OPTION"},
        ]
    }

    with patch("yfinance.Tickers", return_value=mock_tickers):
        resp = client.post("/api/paper-quotes", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "quotes" in data
        assert "NVDA" in data["quotes"]
        assert future_contract in data["quotes"]
        assert data["quotes"]["NVDA"]["valid"] is True
        assert data["quotes"]["NVDA"]["current_price"] == 125.50
        assert data["quotes"][future_contract]["current_price"] == 4.50
        assert data["quotes"][future_contract]["is_expired"] is False


def test_api_paper_quotes_expired_options_settlement():
    """POST /api/paper-quotes automatically settles expired options as ITM or Worthless."""
    client = TestClient(app)

    # Underlying NVDA spot is 130.00
    mock_fast_nvda = MagicMock(last_price=130.00, previous_close=128.00)
    mock_ticker_nvda = MagicMock(fast_info=mock_fast_nvda)

    mock_tickers = MagicMock()
    mock_tickers.tickers.get.side_effect = lambda s: mock_ticker_nvda if "NVDA" in s else None

    # Past expiration date: 2024-05-17
    # 1) Call with strike 100: spot 130 -> intrinsic 30.00 (ITM)
    # 2) Call with strike 150: spot 130 -> intrinsic 0.00 (Worthless)
    # 3) Put with strike 140: spot 130 -> intrinsic 10.00 (ITM)
    itm_call = "NVDA240517C00100000"
    otm_call = "NVDA240517C00150000"
    itm_put = "NVDA240517P00140000"

    payload = {
        "items": [
            {"contract": itm_call, "asset_type": "OPTION"},
            {"contract": otm_call, "asset_type": "OPTION"},
            {"contract": itm_put, "asset_type": "OPTION"},
        ]
    }

    with patch("yfinance.Tickers", return_value=mock_tickers):
        resp = client.post("/api/paper-quotes", json=payload)
        assert resp.status_code == 200
        quotes = resp.json()["quotes"]

        # ITM Call check
        assert quotes[itm_call]["is_expired"] is True
        assert quotes[itm_call]["settlement_type"] == "EXPIRED_ITM"
        assert quotes[itm_call]["settlement_price"] == 30.00
        assert quotes[itm_call]["current_price"] == 30.00

        # OTM Call check
        assert quotes[otm_call]["is_expired"] is True
        assert quotes[otm_call]["settlement_type"] == "EXPIRED_WORTHLESS"
        assert quotes[otm_call]["settlement_price"] == 0.00
        assert quotes[otm_call]["current_price"] == 0.00

        # ITM Put check
        assert quotes[itm_put]["is_expired"] is True
        assert quotes[itm_put]["settlement_type"] == "EXPIRED_ITM"
        assert quotes[itm_put]["settlement_price"] == 10.00
        assert quotes[itm_put]["current_price"] == 10.00


def test_api_paper_quotes_empty():
    """POST /api/paper-quotes with empty items returns empty quotes map."""
    client = TestClient(app)
    resp = client.post("/api/paper-quotes", json={"items": []})
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"quotes": {}}


def test_api_paper_quotes_get_endpoint():
    """GET /api/paper-quotes?contracts=... remains backwards compatible."""
    client = TestClient(app)
    mock_fast = MagicMock(last_price=130.0, previous_close=128.0)
    mock_ticker = MagicMock(fast_info=mock_fast)
    mock_tickers = MagicMock()
    mock_tickers.tickers.get.return_value = mock_ticker

    with patch("yfinance.Tickers", return_value=mock_tickers):
        resp = client.get("/api/paper-quotes?contracts=NVDA")
        assert resp.status_code == 200
        data = resp.json()
        assert "quotes" in data
        assert "NVDA" in data["quotes"]
        assert data["quotes"]["NVDA"]["current_price"] == 130.0


def test_api_lifespan_starts_worker():
    """FastAPI lifespan starts screener background worker on startup."""
    with TestClient(app) as client:
        resp = client.get("/api/stocks/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["worker_running"] is True


def test_api_health_endpoint_memory_reporting():
    """Health check endpoint returns status ok and memory dictionary."""
    with TestClient(app) as client:
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
        assert "memory" in data


def test_bounded_price_cache_eviction():
    """Verify price data cache evicts oldest entries and remains bounded."""
    from data.price_data import _CACHE, _set_in_cache, _get_from_cache, clear_price_cache, MAX_PRICE_CACHE_ENTRIES
    clear_price_cache()

    for i in range(MAX_PRICE_CACHE_ENTRIES + 10):
        _set_in_cache(f"test_key_{i}", f"test_val_{i}")

    # Cache should never exceed MAX_PRICE_CACHE_ENTRIES
    assert len(_CACHE) <= MAX_PRICE_CACHE_ENTRIES
    clear_price_cache()


def test_api_options_recommendations_endpoint():
    """GET /api/options/recommendations returns 200 OK with categorized curated options."""
    client = TestClient(app)
    resp = client.get("/api/options/recommendations")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "market_regime" in data
    assert "total" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) > 0

    first = data["items"][0]
    assert "symbol" in first
    assert "contract" in first
    assert "option_type" in first
    assert "strike" in first
    assert "dte" in first
    assert "delta" in first
    assert "strategy_category" in first

    # Test filtering by category
    resp_cat = client.get("/api/options/recommendations?category=DIRECTIONAL")
    assert resp_cat.status_code == 200
    for item in resp_cat.json()["items"]:
        assert item["strategy_category"] == "DIRECTIONAL"

    # Test filtering by bias
    resp_bias = client.get("/api/options/recommendations?bias=CALL")
    assert resp_bias.status_code == 200
    for item in resp_bias.json()["items"]:
        assert item["bias"] == "BULLISH" or item["option_type"] == "CALL"
