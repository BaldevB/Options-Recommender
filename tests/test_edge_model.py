"""Tests for the contract edge model, signal changes, and the recommendation journal."""

from datetime import date, timedelta
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from analysis import rec_journal
from analysis.signals import generate_signal, BiasDirection, ConfidenceTier, TradeSignal
from config import OptionsFilterConfig
from options.edge import (
    MarketContext, bs_price, implied_vol_from_price, simulate_exit_outcomes, spans_earnings, vol_regime,
)
from options.suggester import rank_and_filter_contracts, suggest_options, build_option_trade_plan

SPOT = 100.0


def _chain(dtes=(21, 35), iv_quoted=0.90, true_iv=0.32, last_trade_age_days=0.0, is_call=True):
    rows = []
    for dte in dtes:
        exp = (date.today() + timedelta(days=dte)).isoformat()
        for k in range(90, 116, 2):
            px = float(bs_price(SPOT, k, dte / 365, true_iv, is_call))
            rows.append(dict(
                contractSymbol=f"X{dte}{'C' if is_call else 'P'}{k}", strike=float(k),
                bid=round(px * 0.97, 2), ask=round(px * 1.03, 2), volume=500, openInterest=2000,
                impliedVolatility=iv_quoted, dte=dte, expiration=exp,
                lastTradeDate=pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=last_trade_age_days),
            ))
    return pd.DataFrame(rows)


def _ctx(rv=0.32, drift=0.0, earnings=None):
    return MarketContext("X", SPOT, rv, 2.0, drift, 0.6, earnings_date=earnings)


# ---------------------------------------------------------------- pricing + simulation

def test_implied_vol_round_trip():
    px = float(bs_price(SPOT, 105, 30 / 365, 0.41, False))
    assert implied_vol_from_price(px, SPOT, 105, 30, False) == pytest.approx(0.41, abs=1e-3)
    assert implied_vol_from_price(0.0, SPOT, 105, 30, False) is None


def test_simulation_is_roughly_fair_without_edge_and_responds_to_inputs():
    px = float(bs_price(SPOT, 100, 30 / 365, 0.30, True))
    fair = simulate_exit_outcomes(SPOT, 100, px, 0.30, 30, True, _ctx(rv=0.30))
    drift = simulate_exit_outcomes(SPOT, 100, px, 0.30, 30, True, _ctx(rv=0.30, drift=0.0006))
    quiet = simulate_exit_outcomes(SPOT, 100, px, 0.30, 30, True, _ctx(rv=0.20))
    assert abs(fair.expected_return_pct) < 5.0
    assert drift.expected_pnl > fair.expected_pnl
    assert quiet.expected_pnl < fair.expected_pnl  # paying 30% IV for a stock that moves 20% loses
    assert fair.prob_target + fair.prob_stop + fair.prob_time_exit == pytest.approx(100.0, abs=0.2)


def test_vol_regime_and_earnings_span():
    assert vol_regime(0.60, 0.40)["regime"] == "RICH"
    assert vol_regime(0.30, 0.40)["regime"] == "CHEAP"
    assert vol_regime(0.30, 0.0)["regime"] == "UNKNOWN"
    exp = (date.today() + timedelta(days=30)).isoformat()
    assert spans_earnings(exp, date.today() + timedelta(days=10))
    assert not spans_earnings(exp, date.today() + timedelta(days=40))


# ---------------------------------------------------------------- ranker

def test_ranker_resolves_iv_from_mid_and_uses_monte_carlo():
    sug, _ = rank_and_filter_contracts(_chain(), "CALL", SPOT, market_ctx=_ctx())
    assert sug
    top = sug[0]
    assert top.iv_source == "mid_solved"
    assert top.implied_volatility_pct == pytest.approx(32.0, abs=1.0)  # not the bogus 90% quote
    assert top.trade_plan.pop_method == "monte_carlo_exit_rules"
    assert top.edge_score is not None and top.execution_score is not None
    assert top.trade_plan.prob_target_before_stop_pct is not None


def test_ranker_without_context_keeps_legacy_behaviour():
    sug, _ = rank_and_filter_contracts(_chain(iv_quoted=0.32), "CALL", SPOT)
    assert sug and sug[0].iv_source == "yfinance"
    assert sug[0].trade_plan.pop_method == "risk_neutral_expiry"
    assert sug[0].edge_score is None


def test_ranker_drops_stale_quotes():
    sug, audit = rank_and_filter_contracts(_chain(last_trade_age_days=10), "CALL", SPOT, market_ctx=_ctx())
    assert audit["rejected_stale"] > 0


def test_ranker_prefers_expirations_before_earnings():
    earnings = date.today() + timedelta(days=28)  # between the 21- and 35-DTE expirations
    sug, audit = rank_and_filter_contracts(_chain(), "CALL", SPOT, market_ctx=_ctx(earnings=earnings))
    assert sug and all(s.dte == 21 for s in sug)
    assert audit["rejected_spans_earnings"] > 0


def test_ranker_keeps_but_flags_earnings_when_no_alternative():
    earnings = date.today() + timedelta(days=10)
    sug, _ = rank_and_filter_contracts(_chain(dtes=(35,)), "CALL", SPOT, market_ctx=_ctx(earnings=earnings))
    assert sug and sug[0].spans_earnings
    assert any("earnings" in w.lower() for w in sug[0].risk_warnings)


def test_edge_prefers_cheap_options_over_rich_ones():
    cheap, _ = rank_and_filter_contracts(_chain(), "CALL", SPOT, market_ctx=_ctx(rv=0.45))
    rich, _ = rank_and_filter_contracts(_chain(), "CALL", SPOT, market_ctx=_ctx(rv=0.20))
    assert cheap[0].vol_regime == "CHEAP" and rich[0].vol_regime == "RICH"
    assert cheap[0].trade_plan.expected_value_per_contract > rich[0].trade_plan.expected_value_per_contract


def test_suggest_options_judges_elevated_iv_against_realized_vol():
    sig = TradeSignal(symbol="X", bias=BiasDirection.BULLISH, combined_score=0.5, confidence=0.6,
                      confidence_tier=ConfidenceTier.MEDIUM, momentum_score=0.5, sentiment_score=0.0,
                      is_earnings_blackout=False)
    chain = _chain()
    res = suggest_options(sig, SPOT, chain, pd.DataFrame(), market_ctx=_ctx(rv=0.20))
    assert res.vol_regime == "RICH" and res.elevated_iv is True  # 32% IV is "low" in absolute terms
    res2 = suggest_options(sig, SPOT, chain, pd.DataFrame(), market_ctx=_ctx(rv=0.45))
    assert res2.vol_regime == "CHEAP" and res2.elevated_iv is False


def test_trade_plan_targets_are_on_the_right_side():
    for is_call in (True, False):
        plan = build_option_trade_plan(
            spot_price=SPOT, strike=100.0, bid=3.4, ask=3.6, mid_price=3.5, delta=0.5 if is_call else -0.5,
            gamma=0.03, theta=-0.06, dte=30, iv_pct=30.0, is_call=is_call, contracts=1, total_dollar_risk=350,
            stop_loss_px=1.75, stop_loss_dollar=175, breakeven_px=103.5 if is_call else 96.5,
        )
        if is_call:
            assert SPOT < plan.tp1_underlying_target < plan.tp2_underlying_target < plan.tp3_underlying_target
            assert plan.underlying_invalidation_price < SPOT
        else:
            assert SPOT > plan.tp1_underlying_target > plan.tp2_underlying_target > plan.tp3_underlying_target
            assert plan.underlying_invalidation_price > SPOT


# ---------------------------------------------------------------- signal

def _momentum(score):
    return MagicMock(symbol="X", momentum_score=score, volume_confirmed=True, multi_timeframe_aligned=False,
                     trend_description="t", rsi=50.0, macd_hist=0.0, volume_ratio=1.2, weekly_trend="NEUTRAL")


def test_sentiment_only_dampens_confidence():
    mom = _momentum(0.40)
    happy = MagicMock(overall_score=0.9, article_count=5, sentiment_label="Bullish")
    sad = MagicMock(overall_score=-0.9, article_count=5, sentiment_label="Bearish")
    base = generate_signal(mom, None)
    assert generate_signal(mom, happy).confidence == pytest.approx(base.confidence)  # no boost
    assert generate_signal(mom, sad).confidence < base.confidence                    # disagreement dampens
    assert generate_signal(mom, sad).bias == BiasDirection.BULLISH                   # direction from momentum


# ---------------------------------------------------------------- journal

def _bars(days, highs, lows, closes):
    idx = pd.to_datetime([d.isoformat() for d in days])
    return pd.DataFrame({"High": highs, "Low": lows, "Close": closes}, index=idx)


def test_journal_records_evaluates_and_reports():
    created = date(2026, 10, 1)
    later = [created + timedelta(days=i) for i in range(1, 30)]
    option_bars = {
        "WIN": _bars(later[:3], [2.2, 2.6, 3.1], [1.9, 2.0, 2.4], [2.1, 2.5, 3.0]),   # hits 3.00 target day 3
        "LOSE": _bars(later[:2], [2.1, 1.6], [1.8, 0.9], [1.9, 1.0]),               # hits 1.00 stop day 2
    }
    under = _bars([created] + later, [0] * 30, [0] * 30, [100.0 + i for i in range(30)])

    def fetch(sym, start):
        return option_bars.get(sym, under)

    items = [
        {"symbol": "X", "contract": c, "entry_mid": 2.0, "target_px": 3.0, "stop_px": 1.0, "max_hold_days": 12,
         "bias": "BULLISH", "expiration": "2026-11-20", "signal_confidence": 0.5, "pred_prob_profit": 55.0}
        for c in ("WIN", "LOSE")
    ]
    import analysis.rec_journal as rj
    orig_now = rj.datetime
    # record "on" the creation date so the dedupe key and created_date match the bars
    class _FixedDT(orig_now):
        @classmethod
        def now(cls, tz=None):
            return orig_now(2026, 10, 1, 15, 0, tzinfo=tz)
    rj.datetime = _FixedDT
    try:
        assert rec_journal.record_recommendations(items, "test") == 2
        assert rec_journal.record_recommendations(items, "test") == 0  # one row per contract per day
    finally:
        rj.datetime = orig_now

    stats = rec_journal.evaluate_pending(fetch=fetch, today=created + timedelta(days=40))
    assert stats["resolved"] == 2
    rep = rec_journal.calibration_report()
    assert rep["scored"] == 2
    assert rep["outcomes"] == {"TARGET": 1, "STOP": 1}
    assert rep["win_rate_pct"] == 50.0
    assert rep["brier_score"] == pytest.approx(((0.55 - 1) ** 2 + 0.55 ** 2) / 2, abs=1e-4)
    assert rep["by_signal_confidence"][0]["avg_directional_ret_10d_pct"] == pytest.approx(10.0, abs=0.01)
    assert rec_journal.calibrated_win_rate(55.0) is None  # bucket far below MIN_BUCKET_SAMPLES


def test_calibration_endpoint():
    from api import app
    resp = TestClient(app).get("/api/calibration")
    assert resp.status_code == 200
    body = resp.json()
    assert body["scored"] == 0 and "by_predicted_probability" in body
