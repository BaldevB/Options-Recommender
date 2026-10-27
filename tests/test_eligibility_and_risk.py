"""Tests for options contract quote validity, strict DTE boundaries, and risk budget sizing."""

import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

from config import RiskManagementConfig, OptionsFilterConfig, DEFAULT_CONFIG
from data.options_data import (
    _clean_chain_df,
    filter_expirations_by_dte,
    get_options_chains,
)
from options.suggester import (
    compute_position_sizing,
    rank_and_filter_contracts,
    build_option_trade_plan,
)


def test_clean_chain_df_does_not_fabricate_bid_ask_from_last_price():
    """Verify that zero bid or ask is NOT synthetically fabricated from lastPrice."""
    raw_df = pd.DataFrame([
        {
            "contractSymbol": "TEST241120C00100000",
            "strike": 100.0,
            "lastPrice": 5.50,
            "bid": 0.0,
            "ask": 0.0,
            "volume": 100,
            "openInterest": 500,
            "impliedVolatility": 0.35,
        },
        {
            "contractSymbol": "TEST241120C00105000",
            "strike": 105.0,
            "lastPrice": 3.20,
            "bid": 3.10,
            "ask": 3.30,
            "volume": 200,
            "openInterest": 800,
            "impliedVolatility": 0.32,
        }
    ])

    cleaned = _clean_chain_df(raw_df, expiration="2026-11-20", dte=24, option_type="CALL")

    # First row had ask 0.0 - it should NOT be filled with lastPrice * 1.01
    row0 = cleaned[cleaned["contractSymbol"] == "TEST241120C00100000"].iloc[0]
    assert row0["ask"] == 0.0
    assert row0["bid"] == 0.0
    assert row0["lastPrice"] == 5.50

    # Second row has genuine bid/ask
    row1 = cleaned[cleaned["contractSymbol"] == "TEST241120C00105000"].iloc[0]
    assert row1["bid"] == 3.10
    assert row1["ask"] == 3.30


def test_filter_expirations_by_dte_respects_boundaries_strictly():
    """Verify filter_expirations_by_dte does not silently substitute out-of-bound expirations."""
    # Expirations: today is calculated dynamically in calculate_dte.
    # Suppose we pass dates that are 5 DTE and 60 DTE.
    # If we request min_dte=20, max_dte=40, it should return an empty list, NOT fallback to 5 or 60.
    from datetime import date, timedelta
    today = date.today()
    exp_5d = (today + timedelta(days=5)).strftime("%Y-%m-%d")
    exp_60d = (today + timedelta(days=60)).strftime("%Y-%m-%d")

    result = filter_expirations_by_dte([exp_5d, exp_60d], min_dte=20, max_dte=40)
    assert result == [], "Should return empty list when no expiration falls in range"


def test_get_options_chains_does_not_silently_fallback_to_out_of_bounds_dte():
    """get_options_chains returns empty DataFrames when no expiration matches requested range."""
    with patch("data.options_data.get_available_expirations", return_value=["2026-10-01"]):
        with patch("data.options_data.calculate_dte", return_value=5):
            calls, puts, exps = get_options_chains("TEST", min_dte=20, max_dte=45)
            assert calls.empty
            assert puts.empty
            assert exps == []


def test_compute_position_sizing_returns_zero_when_budget_exceeded():
    """Position sizing returns 0 contracts when contract price exceeds max risk allocation."""
    # Account equity: $5,000, max risk: 1% => Budget = $50.00
    # Contract ask: $3.50 => 1 contract costs $350.00
    risk_cfg = RiskManagementConfig(
        account_equity=5000.0,
        max_risk_pct=0.01,  # $50 budget
        stop_loss_pct=0.50
    )

    contracts, total_loss, stop_px, stop_dollar = compute_position_sizing(3.50, risk_cfg)
    assert contracts == 0, "Contracts must be 0 when budget is less than 1 contract cost"
    assert total_loss == 0.0
    assert stop_dollar == 0.0
    assert stop_px == 1.75  # 50% stop level preserved for reference


def test_compute_position_sizing_sizes_correctly_when_affordable():
    """Position sizing returns exact integer contracts when budget allows."""
    # Account equity: $50,000, max risk: 2% => Budget = $1,000.00
    # Contract ask: $2.00 => 1 contract costs $200.00 => 5 contracts
    risk_cfg = RiskManagementConfig(
        account_equity=50000.0,
        max_risk_pct=0.02,
        stop_loss_pct=0.50
    )

    contracts, total_loss, stop_px, stop_dollar = compute_position_sizing(2.00, risk_cfg)
    assert contracts == 5
    assert total_loss == 1000.0
    assert stop_dollar == 500.0
    assert stop_px == 1.00


def test_build_option_trade_plan_handles_zero_contracts():
    """Trade plan generation handles contracts=0 gracefully without dividing by zero."""
    plan = build_option_trade_plan(
        spot_price=100.0,
        strike=105.0,
        bid=2.40,
        ask=2.60,
        mid_price=2.50,
        delta=0.45,
        gamma=0.02,
        theta=-0.08,
        dte=30,
        iv_pct=35.0,
        is_call=True,
        contracts=0,
        total_dollar_risk=0.0,
        stop_loss_px=1.25,
        stop_loss_dollar=0.0,
        breakeven_px=107.60,
        contract_symbol="TEST261120C00105000"
    )

    assert plan.total_planned_risk == 0.0
    assert plan.max_capital_loss == 0.0
    assert plan.broker_bracket_order["contracts_total"] == 0
    assert plan.broker_bracket_order["tp1_contracts"] == 0
    assert plan.broker_bracket_order["tp2_contracts"] == 0


def test_rank_and_filter_contracts_tracks_unaffordable_risk():
    """Suggestions for contracts that exceed account budget clearly flag 0 contracts and warnings."""
    # Spot = 100, strikes near spot, ask = 8.00 ($800/contract)
    # Budget = 1% of $1,000 = $10.00 => cannot afford
    risk_cfg = RiskManagementConfig(
        account_equity=1000.0,
        max_risk_pct=0.01,
        stop_loss_pct=0.50
    )
    filter_cfg = OptionsFilterConfig(
        min_dte=14,
        max_dte=45,
        min_delta=0.30,
        max_delta=0.55,
        min_bid=0.05,
        min_volume=10,
        min_open_interest=50,
        max_spread_pct_of_mid=0.10,
    )

    df = pd.DataFrame([
        {
            "contractSymbol": "TEST261120C00100000",
            "strike": 100.0,
            "bid": 7.80,
            "ask": 8.00,
            "volume": 500,
            "openInterest": 1200,
            "impliedVolatility": 0.30,
            "dte": 25,
            "expiration": "2026-11-20",
        }
    ])

    suggestions, audit = rank_and_filter_contracts(
        df, option_type="CALL", spot_price=100.0, filter_cfg=filter_cfg, risk_cfg=risk_cfg
    )

    assert len(suggestions) == 1
    sug = suggestions[0]
    assert sug.suggested_contracts == 0
    assert sug.total_dollar_risk == 0.0
    assert any("exceeds" in w.lower() or "budget" in w.lower() for w in sug.risk_warnings)
