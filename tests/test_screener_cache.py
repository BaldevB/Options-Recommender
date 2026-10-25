import threading
import time
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

from analysis.stock_suggester import TradeHorizon, StockTradePlan, StockRecommendation


def _create_mock_recommendation(
    symbol: str,
    name: str,
    sector: str,
    horizon: TradeHorizon,
    score: float,
    price: float = 100.0,
    volume_ratio: float = 1.0,
    rsi: float = 55.0,
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
        horizon=horizon,
        action="STRONG BUY" if score >= 75 else ("BUY ACCUMULATE" if score >= 58 else "HOLD"),
        score=score,
        confidence=0.85,
        momentum_score=0.45,
        sentiment_score=0.20,
        trade_plan=plan,
        rationale=[f"Test rationale for {symbol}"],
    )


def test_screener_cache_query_and_filter():
    from analysis.screener_cache import StockScreenerCache

    cache = StockScreenerCache()

    # Seed cache with known items
    item_nvda = _create_mock_recommendation("NVDA", "NVIDIA Corporation", "technology", TradeHorizon.SWING, 85.0)
    item_aapl = _create_mock_recommendation("AAPL", "Apple Inc.", "technology", TradeHorizon.LONG_TERM, 78.0)
    item_jnj = _create_mock_recommendation("JNJ", "Johnson & Johnson", "healthcare", TradeHorizon.LONG_TERM, 65.0)
    item_pfe = _create_mock_recommendation("PFE", "Pfizer Inc.", "healthcare", TradeHorizon.SWING, 52.0)
    item_xom = _create_mock_recommendation("XOM", "Exxon Mobil", "energy", TradeHorizon.SWING, 72.0)

    cache._set_cached_items([item_nvda, item_aapl, item_jnj, item_pfe, item_xom])

    # 1. Filter by sector "technology"
    tech_res = cache.get_recommendations(sector="technology")
    assert tech_res["total"] == 2
    symbols = [item["symbol"] for item in tech_res["items"]]
    assert "NVDA" in symbols
    assert "AAPL" in symbols

    # 2. Filter by horizon "SWING"
    swing_res = cache.get_recommendations(horizon="SWING")
    assert swing_res["total"] == 3
    swing_syms = [item["symbol"] for item in swing_res["items"]]
    assert set(swing_syms) == {"NVDA", "PFE", "XOM"}

    # 3. Filter by both sector and horizon
    tech_swing = cache.get_recommendations(sector="technology", horizon="SWING")
    assert tech_swing["total"] == 1
    assert tech_swing["items"][0]["symbol"] == "NVDA"

    # 4. Search query
    search_res = cache.get_recommendations(search="johnson")
    assert search_res["total"] == 1
    assert search_res["items"][0]["symbol"] == "JNJ"

    # Search by ticker
    search_nvda = cache.get_recommendations(search="nvda")
    assert search_nvda["total"] == 1
    assert search_nvda["items"][0]["symbol"] == "NVDA"


def test_screener_cache_breakout_filter():
    from analysis.screener_cache import StockScreenerCache

    cache = StockScreenerCache()
    item_breakout = {
        "symbol": "PLTR",
        "name": "Palantir Technologies",
        "sector": "technology",
        "horizon": "SWING",
        "action": "STRONG BUY",
        "score": 89.0,
        "volume_ratio": 1.75,
        "momentum_score": 0.65,
        "price": 42.0,
        "trade_plan": {
            "entry_zone": [41.5, 42.5],
            "current_price": 42.0,
            "tp1": 46.0,
            "tp2": 50.0,
            "stop_loss": 39.5,
            "risk_reward_ratio": 1.6,
            "invalidation_pct": 5.9,
            "tp1_pct": 9.5,
            "tp2_pct": 19.0,
        },
    }
    item_quiet = {
        "symbol": "SO",
        "name": "Southern Company",
        "sector": "utilities",
        "horizon": "LONG_TERM",
        "action": "HOLD",
        "score": 50.0,
        "volume_ratio": 0.85,
        "momentum_score": 0.05,
        "price": 85.0,
        "trade_plan": {
            "entry_zone": [84.0, 86.0],
            "current_price": 85.0,
            "tp1": 90.0,
            "tp2": 95.0,
            "stop_loss": 82.0,
            "risk_reward_ratio": 1.6,
            "invalidation_pct": 3.5,
            "tp1_pct": 5.8,
            "tp2_pct": 11.7,
        },
    }
    cache._set_cached_items([item_breakout, item_quiet])

    breakout_res = cache.get_recommendations(horizon="breakout")
    assert breakout_res["total"] == 1
    assert breakout_res["items"][0]["symbol"] == "PLTR"


def test_screener_cache_sorting():
    from analysis.screener_cache import StockScreenerCache

    cache = StockScreenerCache()
    item_a = {
        "symbol": "AAA",
        "name": "Triple A",
        "sector": "technology",
        "horizon": "SWING",
        "score": 60.0,
        "price": 300.0,
        "volume_ratio": 1.2,
        "trade_plan": {"current_price": 300.0, "tp1_pct": 5.0, "risk_reward_ratio": 1.5},
    }
    item_b = {
        "symbol": "BBB",
        "name": "Triple B",
        "sector": "technology",
        "horizon": "SWING",
        "score": 90.0,
        "price": 50.0,
        "volume_ratio": 2.5,
        "trade_plan": {"current_price": 50.0, "tp1_pct": 12.0, "risk_reward_ratio": 2.2},
    }
    cache._set_cached_items([item_a, item_b])

    # Sort by score desc -> BBB (90) then AAA (60)
    by_score = cache.get_recommendations(sort_by="score")
    assert by_score["items"][0]["symbol"] == "BBB"

    # Sort by symbol asc -> AAA then BBB
    by_sym = cache.get_recommendations(sort_by="symbol")
    assert by_sym["items"][0]["symbol"] == "AAA"

    # Sort by price desc -> AAA (300) then BBB (50)
    by_price = cache.get_recommendations(sort_by="price")
    assert by_price["items"][0]["symbol"] == "AAA"

    # Sort by volume_ratio desc -> BBB (2.5) then AAA (1.2)
    by_vol = cache.get_recommendations(sort_by="volume_ratio")
    assert by_vol["items"][0]["symbol"] == "BBB"


def test_screener_cache_pagination():
    from analysis.screener_cache import StockScreenerCache

    cache = StockScreenerCache()
    items = [
        _create_mock_recommendation(f"SYM{i}", f"Company {i}", "technology", TradeHorizon.SWING, float(i))
        for i in range(1, 26)  # 25 items
    ]
    cache._set_cached_items(items)

    # Page 1: limit 10, offset 0 -> returns items 0 to 9, sorted by score desc (25 down to 16)
    page1 = cache.get_recommendations(limit=10, offset=0, sort_by="score")
    assert page1["total"] == 25
    assert len(page1["items"]) == 10
    assert page1["items"][0]["symbol"] == "SYM25"
    assert page1["items"][9]["symbol"] == "SYM16"

    # Page 2: limit 10, offset 10 -> returns items 10 to 19 (15 down to 6)
    page2 = cache.get_recommendations(limit=10, offset=10, sort_by="score")
    assert len(page2["items"]) == 10
    assert page2["items"][0]["symbol"] == "SYM15"
    assert page2["items"][9]["symbol"] == "SYM6"

    # Page 3: limit 10, offset 20 -> returns remaining 5 items (5 down to 1)
    page3 = cache.get_recommendations(limit=10, offset=20, sort_by="score")
    assert len(page3["items"]) == 5
    assert page3["items"][0]["symbol"] == "SYM5"
    assert page3["items"][4]["symbol"] == "SYM1"


def test_screener_cache_thread_safe_update():
    from analysis.screener_cache import StockScreenerCache

    cache = StockScreenerCache()
    initial_items = [
        _create_mock_recommendation(f"INIT{i}", f"Initial {i}", "technology", TradeHorizon.SWING, 50.0)
        for i in range(10)
    ]
    cache._set_cached_items(initial_items)

    errors = []
    stop_event = threading.Event()

    def reader_worker():
        while not stop_event.is_set():
            try:
                res = cache.get_recommendations(limit=10)
                assert isinstance(res, dict)
                assert "items" in res
                assert "total" in res
                assert res["total"] >= 10
            except Exception as e:
                errors.append(e)
            time.sleep(0.001)

    def writer_worker():
        for cycle in range(5):
            new_items = [
                _create_mock_recommendation(f"CYC{cycle}_{i}", f"Company {cycle}_{i}", "technology", TradeHorizon.SWING, 60.0 + i)
                for i in range(15)
            ]
            cache._set_cached_items(new_items)
            time.sleep(0.005)

    reader_threads = [threading.Thread(target=reader_worker) for _ in range(3)]
    writer_thread = threading.Thread(target=writer_worker)

    for t in reader_threads:
        t.start()
    writer_thread.start()

    writer_thread.join()
    stop_event.set()
    for t in reader_threads:
        t.join()

    assert len(errors) == 0, f"Thread errors encountered: {errors}"
    final_res = cache.get_recommendations()
    assert final_res["total"] == 15


def test_screener_cache_get_analysis():
    from analysis.screener_cache import StockScreenerCache

    cache = StockScreenerCache()
    item = _create_mock_recommendation("NVDA", "NVIDIA Corporation", "technology", TradeHorizon.SWING, 88.0, price=125.0)
    cache._set_cached_items([item])

    # In cache
    analysis = cache.get_analysis("NVDA")
    assert analysis is not None
    assert analysis["symbol"] == "NVDA"
    assert analysis["score"] == 88.0
    assert analysis["trade_plan"]["current_price"] == 125.0

    # Not in cache and mock on-demand
    with patch("analysis.screener_cache.fetch_single_stock_analysis", return_value=None):
        not_found = cache.get_analysis("NONEXISTENT")
        assert not_found is None


def test_screener_cache_get_status():
    from analysis.screener_cache import StockScreenerCache

    cache = StockScreenerCache()
    status = cache.get_status()
    assert "status" in status
    assert "cached_stocks" in status
    assert "total_stocks" in status
    assert "is_refreshing" in status


def test_screener_cache_refresh_with_mock_data():
    from analysis.screener_cache import StockScreenerCache

    cache = StockScreenerCache()

    # Create dummy 30-day historical dataframe for 2 tickers (NVDA, AAPL)
    dates = pd.date_range("2026-01-01", periods=30, freq="B")
    cols = pd.MultiIndex.from_tuples([
        ("NVDA", "Open"), ("NVDA", "High"), ("NVDA", "Low"), ("NVDA", "Close"), ("NVDA", "Volume"),
        ("AAPL", "Open"), ("AAPL", "High"), ("AAPL", "Low"), ("AAPL", "Close"), ("AAPL", "Volume"),
    ], names=["Ticker", "Price"])

    data = np.ones((30, 10)) * 100.0
    data[:, 3] = np.linspace(100, 120, 30)  # NVDA Close rising
    data[:, 4] = 1000000                     # NVDA Volume
    data[:, 8] = np.linspace(150, 160, 30)  # AAPL Close rising
    data[:, 9] = 2000000                     # AAPL Volume

    mock_df = pd.DataFrame(data, index=dates, columns=cols)

    with patch("yfinance.download", return_value=mock_df):
        res = cache.refresh_cache(tickers=["NVDA", "AAPL"])
        assert res["status"] == "success"
        assert res["scanned_stocks"] == 2

    status = cache.get_status()
    assert status["status"] == "ready"
    assert status["cached_stocks"] == 2

    nvda_rec = cache.get_analysis("NVDA")
    assert nvda_rec is not None
    assert nvda_rec["symbol"] == "NVDA"
    assert nvda_rec["score"] > 0


def test_screener_cache_refresh_graceful_on_empty_or_error():
    from analysis.screener_cache import StockScreenerCache

    cache = StockScreenerCache()

    # Mock empty dataframe
    with patch("yfinance.download", return_value=pd.DataFrame()):
        res = cache.refresh_cache(tickers=["XYZ"])
        assert res["status"] == "empty"
        assert res["scanned_stocks"] == 0

    # Mock exception
    with patch("yfinance.download", side_effect=RuntimeError("Network offline")):
        res_err = cache.refresh_cache(tickers=["XYZ"])
        # Should gracefully return empty or error status and not raise
        assert res_err["status"] in ("empty", "error")


def test_screener_cache_background_worker_start_stop():
    from analysis.screener_cache import StockScreenerCache

    cache = StockScreenerCache()
    assert not cache.get_status()["worker_running"]

    cache.start_background_worker(interval_minutes=60)
    assert cache.get_status()["worker_running"]

    # Calling start again should not spawn duplicate threads
    cache.start_background_worker(interval_minutes=60)
    assert cache.get_status()["worker_running"]

    cache.stop_background_worker(timeout=2.0)
    assert not cache.get_status()["worker_running"]


def test_global_singleton_getter():
    from analysis.screener_cache import get_screener_cache

    cache1 = get_screener_cache()
    cache2 = get_screener_cache()
    assert cache1 is cache2


def test_analysis_package_exports():
    import analysis

    assert hasattr(analysis, "StockScreenerCache")
    assert hasattr(analysis, "get_screener_cache")
    assert hasattr(analysis, "fetch_single_stock_analysis")


def test_screener_cache_strategy_filter():
    from analysis.screener_cache import StockScreenerCache
    cache = StockScreenerCache()
    items = [
        {
            "symbol": "LEAD",
            "name": "Market Leader",
            "sector": "technology",
            "score": 90.0,
            "relative_strength_score": 88.0,
            "distance_from_52w_high_pct": -1.5,
            "strategy_tag": "RS_LEADER",
            "ma_alignment": "FULL_BULLISH",
            "rsi": 64.0,
            "horizon": "SWING",
            "action": "STRONG BUY",
            "trade_plan": {"current_price": 150.0, "tp1_pct": 12.0},
        },
        {
            "symbol": "DIP",
            "name": "Dip Buy Co",
            "sector": "healthcare",
            "score": 65.0,
            "relative_strength_score": 55.0,
            "distance_from_52w_high_pct": -18.0,
            "strategy_tag": "PULLBACK_DIP",
            "ma_alignment": "ABOVE_50DMA",
            "rsi": 38.0,
            "horizon": "LONG_TERM",
            "action": "BUY ACCUMULATE",
            "trade_plan": {"current_price": 80.0, "tp1_pct": 18.0},
        },
    ]
    cache._set_cached_items(items)

    rs_res = cache.get_recommendations(strategy="rs_leaders")
    assert rs_res["total"] == 1
    assert rs_res["items"][0]["symbol"] == "LEAD"

    dip_res = cache.get_recommendations(strategy="pullback")
    assert dip_res["total"] == 1
    assert dip_res["items"][0]["symbol"] == "DIP"
