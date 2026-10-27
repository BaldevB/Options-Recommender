"""Unit and Integration tests for Dynamic On-Demand Options Recommendation Endpoint."""

from unittest.mock import patch
import pandas as pd
import numpy as np
import pytest
from fastapi.testclient import TestClient

from api import app


def _mock_quote(symbol: str = "NVDA", price: float = 120.0) -> dict:
    return {
        "symbol": symbol,
        "current_price": price,
        "previous_close": price * 0.98,
        "change": price * 0.02,
        "change_percent": 2.04,
        "day_high": price * 1.01,
        "day_low": price * 0.98,
        "volume": 25000000,
        "fifty_two_week_high": price * 1.10,
        "fifty_two_week_low": price * 0.70,
        "valid": True,
    }


def _mock_history(base_price: float = 120.0, upward: bool = True, length: int = 40) -> pd.DataFrame:
    dates = pd.date_range(end="2026-10-27", periods=length, freq="D")
    trend = np.linspace(0.85, 1.0, length) if upward else np.linspace(1.15, 1.0, length)
    prices = base_price * trend
    df = pd.DataFrame(
        {
            "Open": prices * 0.99,
            "High": prices * 1.02,
            "Low": prices * 0.98,
            "Close": prices,
            "Volume": [1000000] * length,
        },
        index=dates,
    )
    return df


def _mock_options_chains():
    calls_df = pd.DataFrame(
        [
            {
                "contractSymbol": "NVDA261120C00120000",
                "expiration": "2026-11-20",
                "dte": 30,
                "type": "CALL",
                "strike": 120.0,
                "lastPrice": 5.10,
                "bid": 5.00,
                "ask": 5.20,
                "spread": 0.20,
                "spread_ratio": 0.038,
                "volume": 600,
                "openInterest": 1200,
                "impliedVolatility": 0.40,
                "inTheMoney": False,
            },
            {
                "contractSymbol": "NVDA261120C00125000",
                "expiration": "2026-11-20",
                "dte": 30,
                "type": "CALL",
                "strike": 125.0,
                "lastPrice": 3.10,
                "bid": 3.00,
                "ask": 3.20,
                "spread": 0.20,
                "spread_ratio": 0.062,
                "volume": 400,
                "openInterest": 900,
                "impliedVolatility": 0.38,
                "inTheMoney": False,
            },
        ]
    )
    puts_df = pd.DataFrame(
        [
            {
                "contractSymbol": "NVDA261120P00120000",
                "expiration": "2026-11-20",
                "dte": 30,
                "type": "PUT",
                "strike": 120.0,
                "lastPrice": 5.10,
                "bid": 5.00,
                "ask": 5.20,
                "spread": 0.20,
                "spread_ratio": 0.038,
                "volume": 600,
                "openInterest": 1200,
                "impliedVolatility": 0.40,
                "inTheMoney": False,
            },
            {
                "contractSymbol": "NVDA261120P00115000",
                "expiration": "2026-11-20",
                "dte": 30,
                "type": "PUT",
                "strike": 115.0,
                "lastPrice": 3.10,
                "bid": 3.00,
                "ask": 3.20,
                "spread": 0.20,
                "spread_ratio": 0.062,
                "volume": 400,
                "openInterest": 900,
                "impliedVolatility": 0.38,
                "inTheMoney": False,
            },
        ]
    )
    return calls_df, puts_df, [("2026-11-20", 30)]


def test_api_options_recommend_valid_stock():
    """GET /api/options/recommend?ticker=NVDA returns 200 with single_leg and vertical_spread."""
    client = TestClient(app)
    calls_df, puts_df, exps = _mock_options_chains()

    with patch("api.get_current_quote", return_value=_mock_quote("NVDA", 120.0)), \
         patch("api.get_price_history", return_value=_mock_history(120.0, upward=True)), \
         patch("api.get_options_chains", return_value=(calls_df, puts_df, exps)):

        resp = client.get("/api/options/recommend?ticker=NVDA")
        assert resp.status_code == 200
        data = resp.json()

        assert data["symbol"] == "NVDA"
        assert data["stock_price"] == 120.0
        assert data["bias"] in ("BULLISH", "BEARISH")

        # Verify single_leg structure
        assert data["single_leg"] is not None
        assert "strike" in data["single_leg"]
        assert "delta" in data["single_leg"]
        assert "breakeven" in data["single_leg"]
        assert "pop_pct" in data["single_leg"]
        assert data["single_leg"]["trade_plan"] is not None
        assert "tp1" in data["single_leg"]["trade_plan"]
        assert "stop_loss" in data["single_leg"]["trade_plan"]

        # Verify vertical_spread structure
        assert data["vertical_spread"] is not None
        assert "long_strike" in data["vertical_spread"]
        assert "short_strike" in data["vertical_spread"]
        assert "net_debit" in data["vertical_spread"]
        assert "max_profit" in data["vertical_spread"]
        assert "risk_reward_ratio" in data["vertical_spread"] or "rr" in data["vertical_spread"]


def test_api_options_recommend_missing_chain():
    """GET /api/options/recommend returns 404 or has_options: false when options are missing."""
    client = TestClient(app)

    with patch("api.get_current_quote", return_value=_mock_quote("NOOPT", 50.0)), \
         patch("api.get_price_history", return_value=_mock_history(50.0)), \
         patch("api.get_options_chains", return_value=(pd.DataFrame(), pd.DataFrame(), [])):

        resp = client.get("/api/options/recommend?ticker=NOOPT")
        assert resp.status_code == 404 or (resp.status_code == 200 and resp.json().get("has_options") is False)
        if resp.status_code == 404:
            detail = resp.json().get("detail", "").lower()
            assert "option" in detail or "chain" in detail or "noopt" in detail


def test_api_options_recommend_respects_bias():
    """GET /api/options/recommend?ticker=NVDA&bias=BEARISH recommends a PUT contract."""
    client = TestClient(app)
    calls_df, puts_df, exps = _mock_options_chains()

    with patch("api.get_current_quote", return_value=_mock_quote("NVDA", 120.0)), \
         patch("api.get_price_history", return_value=_mock_history(120.0, upward=True)), \
         patch("api.get_options_chains", return_value=(calls_df, puts_df, exps)):

        resp = client.get("/api/options/recommend?ticker=NVDA&bias=BEARISH")
        assert resp.status_code == 200
        data = resp.json()

        assert data["bias"] == "BEARISH"
        assert data["single_leg"] is not None
        opt_type = data["single_leg"].get("type") or data["single_leg"].get("option_type")
        assert opt_type == "PUT"
