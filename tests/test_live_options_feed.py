"""Tests for live options feed, dynamic VIX regime, confidence preservation, and honest empty states."""

from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from api import app
from analysis.signals import BiasDirection, ConfidenceTier, TradeSignal
from analysis.momentum import MomentumResult


@pytest.fixture
def client():
    return TestClient(app)


def test_options_recommendations_endpoint_includes_live_metadata(client):
    """GET /api/options/recommendations returns transparent metadata: data_source, retrieved_at_utc, disclaimer."""
    with patch("api._get_live_options_recommendations", return_value=[]):
        with patch("api.get_current_quote", return_value={"valid": False}):
            resp = client.get("/api/options/recommendations")
            assert resp.status_code == 200
            data = resp.json()
            assert "data_source" in data
            assert "retrieved_at_utc" in data
            assert "disclaimer" in data
            assert "yfinance" in data["data_source"].lower()
            assert isinstance(data["items"], list)


def test_options_recommendations_dynamic_vix_regime_live(client):
    """GET /api/options/recommendations computes market_regime dynamically from live ^VIX quote."""
    mock_vix_quote = {
        "valid": True,
        "current_price": 18.45,
        "symbol": "^VIX",
    }
    with patch("api.get_current_quote", return_value=mock_vix_quote):
        with patch("api._get_live_options_recommendations", return_value=[]):
            resp = client.get("/api/options/recommendations")
            assert resp.status_code == 200
            regime = resp.json().get("market_regime")
            assert regime is not None
            assert regime["vix"] == 18.45
            assert regime["status"] == "live"
            assert "Moderate" in regime["regime"] or "Balanced" in regime["regime"]


def test_options_recommendations_dynamic_vix_regime_unavailable(client):
    """When ^VIX is unavailable, market_regime does not fabricate 15.6 and reports status=unavailable."""
    mock_bad_quote = {
        "valid": False,
        "current_price": 0.0,
        "symbol": "^VIX",
    }
    with patch("api.get_current_quote", return_value=mock_bad_quote):
        with patch("api._get_live_options_recommendations", return_value=[]):
            resp = client.get("/api/options/recommendations")
            assert resp.status_code == 200
            regime = resp.json().get("market_regime")
            assert regime is not None
            assert regime["vix"] is None
            assert regime["status"] == "unavailable"


def test_options_recommend_preserves_actual_signal_strength(client):
    """GET /api/options/recommend preserves genuine signal confidence and does not force 0.85."""
    mock_stock_quote = {
        "valid": True,
        "current_price": 100.0,
        "symbol": "MOCK",
        "name": "Mock Inc.",
        "change_percent": 0.5,
    }

    mock_mom = MagicMock(
        momentum_score=25.0,  # Weak momentum
        trend_description="Weak sideways",
        rsi=48.0,
        macd_hist=-0.05,
        macd_line=0.0,
        macd_signal=0.05,
        sma_short=99.0,
        sma_long=101.0,
        volume_ratio=0.8,
        volume_confirmed=False,
        weekly_trend="Neutral",
        multi_timeframe_aligned=False,
    )

    weak_signal = TradeSignal(
        symbol="MOCK",
        bias=BiasDirection.NEUTRAL,
        combined_score=0.15,
        confidence=0.32,  # Actual weak confidence
        confidence_tier=ConfidenceTier.LOW,
        momentum_score=25.0,
        sentiment_score=0.0,
        is_earnings_blackout=False,
        rationale=["Weak sideways consolidation"],
    )

    import pandas as pd
    calls_df = pd.DataFrame([
        {
            "contractSymbol": "MOCK261120C00100000",
            "strike": 100.0,
            "bid": 2.50,
            "ask": 2.70,
            "volume": 200,
            "openInterest": 500,
            "impliedVolatility": 0.30,
            "dte": 25,
            "expiration": "2026-11-20",
        }
    ])
    puts_df = pd.DataFrame()

    with patch("api.get_current_quote", return_value=mock_stock_quote), \
         patch("api.get_price_history", return_value=pd.DataFrame({"Close": [100.0]*20})), \
         patch("api.analyze_momentum", return_value=mock_mom), \
         patch("api.generate_signal", return_value=weak_signal), \
         patch("api.get_options_chains", return_value=(calls_df, puts_df, [("2026-11-20", 25)])):
        
        resp = client.get("/api/options/recommend?symbol=MOCK")
        assert resp.status_code == 200
        data = resp.json()
        # Confidence must reflect weak/moderate confidence, NOT fabricated 0.85 / 85%
        assert data["signal"]["confidence_pct"] <= 50.0
        assert data["signal"]["confidence_tier"] != "HIGH"
