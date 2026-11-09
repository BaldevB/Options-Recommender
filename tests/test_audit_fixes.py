"""Regression tests for bugs found in the 2026-11 code audit."""

from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

import api
from api import app
from analysis.signals import BiasDirection, ConfidenceTier, TradeSignal


@pytest.fixture
def client():
    return TestClient(app)


def _fake_tickers(prices):
    """Stand-in for yfinance.Tickers: symbol -> last price."""
    tickers = {}
    for sym, px in prices.items():
        t = MagicMock()
        t.fast_info = MagicMock(last_price=px, previous_close=px)
        tickers[sym] = t
    return MagicMock(tickers=tickers)


def test_paper_quotes_prices_option_by_contract_not_underlying(client):
    occ = "NVDA301220C00230000"  # far-future expiration so it is not settled
    fake = _fake_tickers({"NVDA": 180.0, occ: 4.5})
    with patch("yfinance.Tickers", return_value=fake):
        resp = client.post("/api/paper-quotes", json={"items": [
            {"contract": occ, "symbol": "NVDA", "ticker": "NVDA", "asset_type": "OPTION"},
        ]})
    q = resp.json()["quotes"][occ]
    assert q["current_price"] == 4.5
    assert q["underlying_spot"] == 180.0


def test_paper_quotes_unpriceable_option_is_invalid_not_stock_price(client):
    label = "NVDA BULL_CALL 180/190"
    fake = _fake_tickers({"NVDA": 180.0})
    with patch("yfinance.Tickers", return_value=fake):
        resp = client.post("/api/paper-quotes", json={"items": [
            {"contract": label, "symbol": "NVDA", "ticker": "NVDA", "asset_type": "OPTION",
             "expiration": "2030-12-20", "strike": 180},
        ]})
    q = resp.json()["quotes"][label.upper()]
    assert q["valid"] is False
    assert q["current_price"] == 0.0


def test_ticker_scoped_refresh_merges_instead_of_wiping():
    from analysis.screener_cache import StockScreenerCache

    cache = StockScreenerCache()
    cache._set_cached_items([{"symbol": "MSFT", "score": 70.0}])

    dates = pd.date_range("2026-01-01", periods=30, freq="B")
    cols = pd.MultiIndex.from_tuples(
        [("NVDA", c) for c in ("Open", "High", "Low", "Close", "Volume")], names=["Ticker", "Price"]
    )
    data = np.ones((30, 5)) * 100.0
    data[:, 3] = np.linspace(100, 120, 30)
    data[:, 4] = 1_000_000
    with patch("yfinance.download", return_value=pd.DataFrame(data, index=dates, columns=cols)):
        cache.refresh_cache(tickers=["NVDA"])
    assert cache.get_status()["cached_stocks"] == 2

    # A ticker refresh that finds nothing must not empty the screener
    with patch("yfinance.download", return_value=pd.DataFrame()):
        cache.refresh_cache(tickers=["ZZZZ"])
    assert cache.get_status()["cached_stocks"] == 2
    assert cache.get_analysis("MSFT") is not None


def test_stock_analysis_short_history_returns_422(client):
    quote = {"valid": True, "current_price": 10.0, "symbol": "IPO", "name": "IPO"}
    with patch("api.get_current_quote", return_value=quote), \
         patch("api.get_price_history", return_value=pd.DataFrame({"Close": [10.0] * 5})), \
         patch("api.get_candles_data", return_value=[]), \
         patch("api.get_earnings_info", return_value=MagicMock()), \
         patch("api.analyze_momentum", return_value=None):
        resp = client.get("/api/stock-analysis?ticker=IPO")
    assert resp.status_code == 422


def test_monte_carlo_unknown_ticker_returns_404(client):
    with patch("api.get_current_quote", return_value={"valid": False, "current_price": 0.0}), \
         patch("api.get_price_history", return_value=None):
        resp = client.get("/api/stocks/monte-carlo?symbol=ZZZZ")
    assert resp.status_code == 404


def test_options_recommend_small_risk_pct_is_percent(client):
    signal = TradeSignal(
        symbol="MOCK", bias=BiasDirection.BULLISH, combined_score=0.5, confidence=0.6,
        confidence_tier=ConfidenceTier.MEDIUM, momentum_score=0.5, sentiment_score=0.0,
        is_earnings_blackout=False, rationale=[],
    )
    quote = {"valid": True, "current_price": 100.0, "symbol": "MOCK", "name": "Mock", "change_percent": 0.0}
    calls_df = pd.DataFrame([{
        "contractSymbol": "MOCK301220C00100000", "strike": 100.0, "bid": 2.5, "ask": 2.7,
        "volume": 200, "openInterest": 500, "impliedVolatility": 0.30, "dte": 25, "expiration": "2030-12-20",
    }])
    with patch("api.get_current_quote", return_value=quote), \
         patch("api.get_price_history", return_value=pd.DataFrame({"Close": [100.0] * 20})), \
         patch("api.analyze_momentum", return_value=MagicMock(momentum_score=0.5)), \
         patch("api.generate_signal", return_value=signal), \
         patch("api.get_company_news", return_value=[]), \
         patch("api.get_options_chains", return_value=(calls_df, pd.DataFrame(), [("2030-12-20", 25)])), \
         patch("api.RiskManagementConfig", wraps=api.RiskManagementConfig) as risk_cfg:
        client.get("/api/options/recommend?symbol=MOCK&risk_pct=0.05")
    assert risk_cfg.call_args.kwargs["max_risk_pct"] == pytest.approx(0.0005)


def test_monte_carlo_log_drift_not_double_corrected():
    from analysis.monte_carlo import run_monte_carlo_simulation

    # Flat prices with alternating noise: mean log return ~0, so median path should stay ~flat
    closes = 100.0 * np.exp(np.concatenate([[0.0], np.cumsum(np.tile([0.02, -0.02], 60))]))
    df = pd.DataFrame({"Close": closes})
    res = run_monte_carlo_simulation("X", current_price=float(closes[-1]), df=df,
                                     simulations=4000, forecast_days=60, seed=1)
    # Double-subtracting sigma^2/2 would push the median ~1.2% below spot here
    assert res.median_final_price / res.current_price == pytest.approx(1.0, abs=0.006)
