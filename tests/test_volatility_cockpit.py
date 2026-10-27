"""Tests for Volatility Cockpit metric labeling and data transparency."""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from data.options_data import get_volatility_cockpit


def test_volatility_cockpit_includes_transparent_methodology_and_sources():
    """Verify that get_volatility_cockpit explicitly declares HV benchmark methodology and data source."""
    mock_quote = {
        "valid": True,
        "current_price": 150.0,
        "name": "NVIDIA Corporation",
        "change": 2.50,
        "change_percent": 1.69,
    }

    # Generate 1 year of daily mock prices
    dates = pd.date_range(end="2026-10-27", periods=260)
    prices = [100.0 + i * 0.2 for i in range(260)]
    mock_hist = pd.DataFrame({"Close": prices}, index=dates)

    with patch("data.price_data.get_current_quote", return_value=mock_quote), \
         patch("data.price_data.get_price_history", return_value=mock_hist), \
         patch("yfinance.Ticker") as mock_ticker:

        mock_t = MagicMock()
        mock_t.options = []
        mock_ticker.return_value = mock_t

        res = get_volatility_cockpit("NVDA")

        assert "error" not in res
        assert "data_source" in res
        assert "yfinance" in res["data_source"].lower()
        assert "retrieved_at_utc" in res
        assert "hv_benchmarked_iv_rank" in res
        assert "hv_benchmarked_iv_percentile" in res
        assert "metric_methodology" in res
        assert "Realized Volatility Benchmark" in res["metric_methodology"]
        assert "methodology_disclaimer" in res
        assert res["bid_ask_sizes"] == "unavailable (yfinance standard)"
