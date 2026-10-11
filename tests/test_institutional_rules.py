"""Unit and integration test suite validating institutional options rules:
1. Hard affordability rule & opt-in uncapped sizing guardrails
2. Conservative net expectancy ranking (modeling entry at ask, exit at bid, commissions & slippage)
3. Upgraded liquidity eligibility & 'indicative' quote labeling
4. Unclipped model-implied probability N(d2) & scenario outcomes stress testing
5. Event-aware selection & dividend/macro risk profiling
6. Gated 0DTE rules, market hour cutoffs & FINRA settlement/pin risk disclosure
7. Walk-forward backtesting engine & baseline validation
"""

from datetime import datetime
import math
import unittest
import numpy as np
import pandas as pd

from config import (
    RiskManagementConfig, OptionsFilterConfig, HighRiskOptionsFilterConfig,
    ZeroDteOptionsFilterConfig, DEFAULT_CONFIG
)
from options.suggester import (
    compute_position_sizing,
    calculate_round_trip_friction,
    calculate_net_expectancy,
    calculate_model_implied_probability,
    compute_scenario_outcomes,
    rank_and_filter_contracts,
    build_zero_dte_setup,
    check_0dte_market_session,
    suggest_options,
    OptionSuggestion,
)
from analysis.signals import TradeSignal, BiasDirection, ConfidenceTier
from data.price_data import get_event_risk_profile
from analysis.backtesting import WalkForwardBacktestEngine, detect_market_regime


class TestInstitutionalOptionsRules(unittest.TestCase):

    def setUp(self):
        self.risk_cfg = RiskManagementConfig(
            account_equity=10000.0,
            max_risk_pct=0.01,           # $100 budget
            stop_loss_pct=0.50,
            allow_unaffordable=False,
            allow_uncapped_speculative=False,
            max_contracts_cap=50,
            max_daily_loss_budget=500.0,
            commission_per_contract=0.65,
            slippage_pct=0.02,
            min_net_expectancy=0.0,
        )

    def test_hard_affordability_rejection(self):
        """Rule 1: Hard affordability. If contract cost exceeds budget, return 0 contracts and False."""
        contracts, total_loss, stop_px, stop_dollar, is_affordable = compute_position_sizing(
            contract_cost=5.00,
            risk_cfg=self.risk_cfg
        )
        self.assertFalse(is_affordable)
        self.assertEqual(contracts, 0)
        self.assertEqual(total_loss, 0.0)
        self.assertEqual(stop_dollar, 0.0)

    def test_hard_affordability_when_affordable(self):
        """Rule 1: Sizing when contract is well within risk budget."""
        contracts, total_loss, stop_px, stop_dollar, is_affordable = compute_position_sizing(
            contract_cost=0.80,
            risk_cfg=self.risk_cfg
        )
        self.assertTrue(is_affordable)
        self.assertEqual(contracts, 2)
        self.assertEqual(total_loss, 160.0)
        self.assertEqual(stop_dollar, 80.0)

    def test_uncapped_opt_in_guardrails(self):
        """Rule 1: Uncapped sizing is opt-in only, with max contracts and daily loss guardrails."""
        cfg_capped = RiskManagementConfig(
            account_equity=50000.0,
            max_risk_pct=0.10,          # $5,000 budget
            allow_uncapped_speculative=False,
            max_contracts_cap=25,
            max_daily_loss_budget=400.0,
        )
        contracts_a, _, _, stop_dollar_a, is_aff_a = compute_position_sizing(
            contract_cost=0.20, risk_cfg=cfg_capped, is_uncapped=True
        )
        self.assertTrue(is_aff_a)
        self.assertLessEqual(contracts_a, 25)
        self.assertLessEqual(stop_dollar_a, 400.0)

        cfg_uncapped = RiskManagementConfig(
            account_equity=50000.0,
            max_risk_pct=0.20,          # $10,000 budget
            allow_uncapped_speculative=True,
            max_contracts_cap=30,
            max_daily_loss_budget=500.0,
        )
        contracts_b, _, _, stop_dollar_b, is_aff_b = compute_position_sizing(
            contract_cost=0.10, risk_cfg=cfg_uncapped, is_uncapped=True
        )
        self.assertTrue(is_aff_b)
        self.assertLessEqual(contracts_b, 30)
        self.assertLessEqual(stop_dollar_b, 500.0)

    def test_conservative_round_trip_friction_and_net_ev(self):
        """Rule 2: Conservative execution penalty pricing."""
        ask = 2.50
        bid = 2.30  # $0.20 spread
        friction = calculate_round_trip_friction(
            ask=ask, bid=bid, commission_per_contract=0.65, slippage_pct=0.02
        )
        self.assertEqual(friction, 31.30)

        ev = calculate_net_expectancy(
            entry_cost=ask,
            model_implied_pop=50.0,
            round_trip_friction=friction,
            target_gain_pct=0.50,
            stop_loss_pct=0.50
        )
        self.assertEqual(ev, -31.30)
        self.assertLess(ev, 0.0)

    def test_net_expectancy_rejection_in_filtering(self):
        """Rule 2: Reject contracts whose expected value is <= 0 after round-trip costs."""
        chain_data = pd.DataFrame([{
            "contractSymbol": "NVDA261016C00125000",
            "strike": 125.0,
            "dte": 30,
            "expiration": "2026-10-16",
            "bid": 2.00,
            "ask": 2.80,  # $0.80 spread (> $0.50 max_absolute_spread, huge friction)
            "volume": 200,
            "openInterest": 500,
            "impliedVolatility": 0.45,
            "inTheMoney": False,
        }])
        filter_cfg = OptionsFilterConfig(
            min_delta=0.20,
            max_delta=0.60,
            max_absolute_spread=1.00,  # allow through to test EV rejection
            max_spread_pct_of_mid=0.50,
        )
        risk_cfg = RiskManagementConfig(
            account_equity=100000.0,
            max_risk_pct=0.05,
            min_net_expectancy=0.0
        )
        suggestions, audit = rank_and_filter_contracts(
            chain_data, "CALL", spot_price=120.0, filter_cfg=filter_cfg, risk_cfg=risk_cfg
        )
        self.assertEqual(len(suggestions), 0)
        self.assertGreater(audit.get("rejected_negative_ev", 0), 0)

    def test_unclipped_model_implied_probability(self):
        """Rule 4: N(d2) must NOT be clipped to 5-95%."""
        pop_deep_otm = calculate_model_implied_probability(
            spot=100.0, breakeven=160.0, dte=10, iv=0.25, is_call=True
        )
        self.assertLess(pop_deep_otm, 1.0)
        self.assertGreater(pop_deep_otm, 0.0)

        pop_deep_itm = calculate_model_implied_probability(
            spot=100.0, breakeven=60.0, dte=10, iv=0.25, is_call=True
        )
        self.assertGreater(pop_deep_itm, 98.0)
        self.assertLessEqual(pop_deep_itm, 99.99)

    def test_scenario_outcomes_matrix(self):
        """Rule 4: Multi-factor scenario stress outcomes matrix."""
        scenarios = compute_scenario_outcomes(
            spot=100.0, strike=102.0, dte=30, iv=0.30, is_call=True, entry_price=2.50
        )
        self.assertEqual(len(scenarios), 6)
        names = [s["scenario"] for s in scenarios]
        self.assertIn("Bull Shock (+1σ Move)", names)
        self.assertIn("Bear Shock (-1σ Move)", names)
        self.assertIn("Volatility Expansion (+25% IV)", names)
        self.assertIn("Volatility Crush (-30% IV)", names)
        self.assertIn("Time Decay Half-Life (50% DTE)", names)
        self.assertIn("Expiry Intrinsic Payoff", names)

    def test_indicative_quote_labeling(self):
        """Rule 3: Label results as 'indicative—verify in broker chain'."""
        chain_data = pd.DataFrame([{
            "contractSymbol": "NVDA261016C00120000",
            "strike": 120.0,
            "dte": 30,
            "expiration": "2026-10-16",
            "bid": 3.80,
            "ask": 4.00,  # tight $0.20 spread
            "volume": 500,
            "openInterest": 1200,
            "impliedVolatility": 0.35,
            "inTheMoney": False,
        }])
        filter_cfg = OptionsFilterConfig(
            min_delta=0.30,
            max_delta=0.60,
            max_absolute_spread=0.50,
            max_spread_pct_of_mid=0.10,
            min_volume=25,
            min_open_interest=100,
        )
        risk_cfg = RiskManagementConfig(
            account_equity=100000.0,
            max_risk_pct=0.05,
            min_net_expectancy=-100.0  # pass for quote check
        )
        suggestions, _ = rank_and_filter_contracts(
            chain_data, "CALL", spot_price=120.0, filter_cfg=filter_cfg, risk_cfg=risk_cfg
        )
        self.assertEqual(len(suggestions), 1)
        opt = suggestions[0]
        self.assertTrue(opt.is_indicative)
        self.assertEqual(opt.quote_quality, "indicative—verify in broker chain")
        self.assertTrue(any("indicative" in w.lower() for w in opt.risk_warnings))

    def test_event_risk_profile_index_and_dividends(self):
        """Rule 5: Event-aware selection for index products and dividend dates."""
        profile_spy = get_event_risk_profile("SPY")
        self.assertTrue(profile_spy["is_index_product"])
        self.assertTrue(profile_spy["has_macro_event"])
        self.assertTrue(any(k in profile_spy["macro_event_name"] for k in ["CPI", "FOMC"]))

        profile_aapl = get_event_risk_profile("AAPL")
        self.assertFalse(profile_aapl["is_index_product"])
        self.assertIn("has_dividend_event", profile_aapl)

    def test_zero_dte_gating_and_pin_risk_warnings(self):
        """Rule 6: 0DTE session gating and settlement pin risk warning."""
        zero_cfg = ZeroDteOptionsFilterConfig(enforce_market_hours=True)
        is_open, is_entry, msg = check_0dte_market_session(zero_cfg)
        self.assertIsInstance(is_open, bool)
        self.assertIsInstance(is_entry, bool)
        self.assertIsInstance(msg, str)

        chain_df = pd.DataFrame([{
            "contractSymbol": "SPY261011C00580000",
            "strike": 580.0,
            "dte": 0,
            "expiration": "2026-10-11",
            "bid": 0.85,
            "ask": 0.95,
            "volume": 250,
            "openInterest": 1500,
            "impliedVolatility": 0.18,
            "inTheMoney": False,
        }])
        setup = build_zero_dte_setup(
            chain_df=chain_df,
            option_type="CALL",
            spot_price=580.0,
            zero_dte_cfg=zero_cfg,
            risk_cfg=RiskManagementConfig(account_equity=50000.0, max_risk_pct=0.02),
            symbol="SPY"
        )
        self.assertIsNotNone(setup)
        self.assertEqual(setup.settlement_type, "PHYSICAL")
        self.assertIn("Pin Risk", setup.settlement_risk_warning)
        self.assertEqual(setup.quote_quality, "indicative—verify in broker chain")

    def test_walk_forward_backtest_baseline_comparison(self):
        """Rule 7: Walk-forward backtesting comparison against ATM and Fixed-Delta baselines."""
        dates = pd.date_range("2026-01-01", periods=100, freq="B")
        prices = [100.0]
        np.random.seed(42)
        for _ in range(99):
            prices.append(prices[-1] * (1.0 + np.random.normal(0.001, 0.015)))

        df_bars = pd.DataFrame({"Close": prices, "Open": prices, "High": prices, "Low": prices, "Volume": 1000000}, index=dates)

        engine = WalkForwardBacktestEngine(
            risk_cfg=RiskManagementConfig(account_equity=25000.0, max_risk_pct=0.02)
        )
        result = engine.run_walk_forward("TEST_SYM", df_bars, sample_step_days=15)

        self.assertEqual(result.symbol, "TEST_SYM")
        self.assertGreaterEqual(result.total_regime_bars, 100)
        self.assertIn("Institutional Net EV Selector", result.selector_metrics.strategy_name)
        self.assertIn("Baseline 1: ATM 35 DTE", result.baseline_atm_metrics.strategy_name)
        self.assertIn("Baseline 2: Fixed Delta 0.40", result.baseline_fixed_delta_metrics.strategy_name)
        self.assertIsInstance(result.net_outperformance_vs_atm, float)
        self.assertIn(result.rule_recommendation, ["Keep All Rules", "Refine Rules"])


if __name__ == "__main__":
    unittest.main()
