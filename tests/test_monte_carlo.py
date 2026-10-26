import pytest
import numpy as np
import pandas as pd
from analysis.monte_carlo import (
    MonteCarloResult,
    run_monte_carlo_simulation,
)


def test_monte_carlo_simulation_basic():
    # Run simulation with 500 paths for 20 days
    res = run_monte_carlo_simulation(
        symbol="NVDA",
        current_price=100.0,
        simulations=500,
        forecast_days=20,
        tp1=115.0,
        stop_loss=90.0,
        seed=42,
    )

    assert isinstance(res, MonteCarloResult)
    assert res.symbol == "NVDA"
    assert res.current_price == 100.0
    assert res.simulations == 500
    assert res.forecast_days == 20
    assert res.median_final_price > 0.0
    assert 0.0 <= res.prob_profit <= 100.0
    assert 0.0 <= res.prob_hit_tp1 <= 100.0
    assert 0.0 <= res.prob_hit_stop_loss <= 100.0
    assert 0.0 <= res.win_rate_tp_before_sl <= 100.0
    assert res.var_95_dollar >= 0.0
    assert res.var_99_dollar >= res.var_95_dollar
    assert "p50" in res.percentile_trajectories
    assert "p5" in res.percentile_trajectories
    assert "p95" in res.percentile_trajectories
    assert len(res.percentile_trajectories["p50"]) == 21
    assert len(res.days_labels) == 21
    assert len(res.distribution_bins) > 0


def test_monte_carlo_simulation_with_dataframe():
    # Generate 60 days of historical data with steady upward drift
    dates = pd.date_range("2024-01-01", periods=60, freq="B")
    prices = [100.0 * (1.002 ** i) for i in range(60)]
    df = pd.DataFrame({
        "Close": prices,
        "High": [p * 1.01 for p in prices],
        "Low": [p * 0.99 for p in prices],
        "Volume": [1000000] * 60,
    }, index=dates)

    res = run_monte_carlo_simulation(
        symbol="AAPL",
        current_price=float(prices[-1]),
        df=df,
        simulations=1000,
        forecast_days=30,
        seed=123,
    )

    assert res.annualized_drift > 0.0
    assert res.annualized_volatility > 0.0
    assert res.median_final_price > 0.0
    assert res.expected_return_pct is not None


def test_monte_carlo_reproducibility():
    # Same seed should produce identical trajectories
    res1 = run_monte_carlo_simulation("MSFT", 200.0, simulations=200, forecast_days=15, seed=777)
    res2 = run_monte_carlo_simulation("MSFT", 200.0, simulations=200, forecast_days=15, seed=777)

    assert res1.median_final_price == res2.median_final_price
    assert res1.prob_hit_tp1 == res2.prob_hit_tp1
    assert res1.percentile_trajectories["p50"] == res2.percentile_trajectories["p50"]
