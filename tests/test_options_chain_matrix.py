"""Tests for options chain matrix resilience, spot price fallback, and expiration selection."""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
import pandas as pd
from data.options_data import get_options_chain_matrix, get_available_expirations


def _make_mock_chain():
    calls_data = {
        "contractSymbol": ["TSLA261120C00200000", "TSLA261120C00210000"],
        "strike": [200.0, 210.0],
        "bid": [15.0, 8.0],
        "ask": [15.5, 8.5],
        "lastPrice": [15.2, 8.2],
        "volume": [500, 300],
        "openInterest": [1200, 900],
        "impliedVolatility": [0.45, 0.42],
        "inTheMoney": [True, False],
    }
    puts_data = {
        "contractSymbol": ["TSLA261120P00200000", "TSLA261120P00210000"],
        "strike": [200.0, 210.0],
        "bid": [4.0, 9.0],
        "ask": [4.5, 9.5],
        "lastPrice": [4.2, 9.2],
        "volume": [200, 150],
        "openInterest": [800, 600],
        "impliedVolatility": [0.44, 0.43],
        "inTheMoney": [False, True],
    }
    mock_chain = MagicMock()
    mock_chain.calls = pd.DataFrame(calls_data)
    mock_chain.puts = pd.DataFrame(puts_data)
    return mock_chain


def test_options_chain_matrix_success():
    """Verify that get_options_chain_matrix returns strikes and calculated analytics."""
    mock_quote = {"valid": True, "current_price": 205.0, "name": "Tesla, Inc.", "change": 1.5, "change_percent": 0.74}
    exp_date = "2026-11-20"

    with patch("data.price_data.get_current_quote", return_value=mock_quote), \
         patch("data.options_data.get_available_expirations", return_value=[exp_date]), \
         patch("yfinance.Ticker") as mock_ticker:

        mock_t = MagicMock()
        mock_t.option_chain.return_value = _make_mock_chain()
        mock_ticker.return_value = mock_t

        res = get_options_chain_matrix("TSLA", expiration=exp_date)

        assert "error" not in res or not res["error"]
        assert res["symbol"] == "TSLA"
        assert res["current_price"] == 205.0
        assert res["selected_expiration"] == exp_date
        assert len(res["strikes"]) == 2
        assert res["analytics"]["expected_move"] > 0
        assert res["strikes"][0]["strike"] == 200.0


def test_options_chain_matrix_infers_spot_price_when_quote_is_zero():
    """Verify that if spot price quote returns 0.0, spot is inferred from median strikes."""
    mock_zero_quote = {"valid": False, "current_price": 0.0, "name": "TSLA"}
    exp_date = "2026-11-20"

    with patch("data.price_data.get_current_quote", return_value=mock_zero_quote), \
         patch("data.options_data.get_available_expirations", return_value=[exp_date]), \
         patch("yfinance.Ticker") as mock_ticker:

        mock_t = MagicMock()
        mock_t.fast_info.last_price = None
        mock_t.fast_info.regular_market_price = None
        mock_t.history.return_value = pd.DataFrame()
        mock_t.option_chain.return_value = _make_mock_chain()
        mock_ticker.return_value = mock_t

        res = get_options_chain_matrix("TSLA", expiration=exp_date)

        assert len(res["strikes"]) == 2
        # Strikes are 200.0 and 210.0, median is 205.0
        assert res["current_price"] == 205.0
        assert res["analytics"]["expected_range_low"] > 0


def test_options_chain_matrix_symbol_normalization():
    """Verify that tickers with dots (e.g. BRK.B) are normalized to hyphens."""
    mock_quote = {"valid": True, "current_price": 450.0, "name": "Berkshire"}

    with patch("data.price_data.get_current_quote", return_value=mock_quote) as mock_get_quote, \
         patch("data.options_data.get_available_expirations", return_value=[]):

        res = get_options_chain_matrix("BRK.B")
        assert res["symbol"] == "BRK-B"
        mock_get_quote.assert_called_with("BRK-B")


def test_options_chain_matrix_empty_expirations_returns_clean_state():
    """Verify that when no expirations are available, clean error state is returned without crashing."""
    mock_quote = {"valid": True, "current_price": 100.0, "name": "XYZ Corp"}

    with patch("data.price_data.get_current_quote", return_value=mock_quote), \
         patch("data.options_data.get_available_expirations", return_value=[]):

        res = get_options_chain_matrix("XYZ")
        assert res["error"] == "No options available for XYZ"
        assert res["strikes"] == []
        assert res["available_expirations"] == []
        assert res["current_price"] == 100.0


def test_get_available_expirations_retries_on_failure():
    """Verify that get_available_expirations retries if the first attempt throws an exception."""
    with patch("yfinance.Ticker") as mock_ticker, \
         patch("time.sleep"):

        mock_t1 = MagicMock()
        type(mock_t1).options = PropertyMock(side_effect=Exception("Rate limit"))

        mock_t2 = MagicMock()
        type(mock_t2).options = PropertyMock(return_value=["2026-11-20", "2026-12-18"])

        mock_ticker.side_effect = [mock_t1, mock_t2]

        exps = get_available_expirations("TSLA")
        assert exps == ["2026-11-20", "2026-12-18"]
        assert mock_ticker.call_count == 2
