import pytest
import pandas as pd
from analysis.momentum import MomentumResult
from analysis.sentiment import SentimentResult
from data.price_data import QuoteData
from analysis.stock_suggester import (
    TradeHorizon,
    StockTradePlan,
    StockRecommendation,
    generate_stock_recommendation,
    calculate_stock_shares,
    evaluate_minervini_stage_2,
    evaluate_vcp_squeeze,
    evaluate_accumulation_distribution,
)
from analysis.screener_cache import StockScreenerCache


def _make_dummy_momentum(
    symbol: str = "NVDA",
    last_close: float = 120.0,
    momentum_score: float = 0.55,
    volume_ratio: float = 1.45,
    volume_confirmed: bool = True,
    weekly_trend: str = "BULLISH",
    multi_timeframe_aligned: bool = True,
) -> MomentumResult:
    return MomentumResult(
        symbol=symbol,
        last_close=last_close,
        rsi=62.5,
        macd_line=1.8,
        macd_signal=1.2,
        macd_hist=0.6,
        sma_short=115.0,
        sma_long=108.0,
        volume_ratio=volume_ratio,
        volume_confirmed=volume_confirmed,
        weekly_trend=weekly_trend,
        multi_timeframe_aligned=multi_timeframe_aligned,
        trend_description="Strong Bullish Momentum",
        momentum_score=momentum_score,
        details={
            "rsi_score": 0.25,
            "macd_score": 0.5,
            "ma_score": 0.4,
            "above_sma20": True,
            "above_sma50": True,
            "sma20_above_sma50": True,
            "weekly_sma10": 110.0,
        },
    )


def _make_dummy_sentiment(
    symbol: str = "NVDA",
    overall_score: float = 0.42,
    article_count: int = 5,
) -> SentimentResult:
    return SentimentResult(
        symbol=symbol,
        overall_score=overall_score,
        sentiment_label="Bullish Sentiment",
        article_count=article_count,
        positive_count=4,
        negative_count=0,
        neutral_count=1,
        scored_articles=[],
    )


def test_generate_stock_recommendation_bullish_swing():
    quote = QuoteData(
        symbol="NVDA",
        name="NVIDIA Corporation",
        current_price=120.0,
        previous_close=118.0,
        day_high=121.5,
        day_low=117.5,
        volume=50000000,
        valid=True,
    )
    momentum = _make_dummy_momentum(
        symbol="NVDA",
        last_close=120.0,
        momentum_score=0.55,
        volume_ratio=1.45,
        volume_confirmed=True,
    )
    sentiment = _make_dummy_sentiment(symbol="NVDA", overall_score=0.35)

    rec = generate_stock_recommendation(
        symbol="NVDA",
        quote=quote,
        momentum=momentum,
        sentiment=sentiment,
    )

    assert isinstance(rec, StockRecommendation)
    assert rec.symbol == "NVDA"
    assert rec.horizon == TradeHorizon.SWING
    assert "BUY" in rec.action.upper()
    assert rec.score > 50.0
    assert rec.confidence > 0.0

    plan = rec.trade_plan
    assert isinstance(plan, StockTradePlan)
    assert plan.current_price == 120.0
    assert plan.tp1 > plan.current_price
    assert plan.tp2 > plan.tp1
    assert plan.current_price > plan.stop_loss > 0.0
    assert plan.risk_reward_ratio >= 1.5
    assert plan.tp1_pct > 0.0
    assert plan.tp2_pct > plan.tp1_pct
    assert plan.invalidation_pct > 0.0
    assert len(plan.entry_zone) == 2
    assert plan.entry_zone[0] <= plan.current_price <= plan.entry_zone[1] or plan.entry_zone[0] < plan.entry_zone[1]


def test_generate_stock_recommendation_long_term():
    quote = QuoteData(
        symbol="JNJ",
        name="Johnson & Johnson",
        current_price=160.0,
        previous_close=159.5,
        day_high=160.5,
        day_low=159.0,
        volume=8000000,
        valid=True,
        beta=0.65,
    )
    momentum = _make_dummy_momentum(
        symbol="JNJ",
        last_close=160.0,
        momentum_score=0.28,
        volume_ratio=0.95,
        volume_confirmed=False,
        weekly_trend="BULLISH",
        multi_timeframe_aligned=True,
    )
    sentiment = _make_dummy_sentiment(symbol="JNJ", overall_score=0.20)

    # Low beta + steady multi-timeframe weekly alignment should produce LONG_TERM
    rec_lt = generate_stock_recommendation(
        symbol="JNJ",
        quote=quote,
        momentum=momentum,
        sentiment=sentiment,
        beta=0.65,
    )

    assert rec_lt.horizon == TradeHorizon.LONG_TERM

    # Long term setup should have wider targets than a swing setup with same price & ATR
    rec_swing = generate_stock_recommendation(
        symbol="JNJ",
        quote=quote,
        momentum=momentum,
        sentiment=sentiment,
        horizon=TradeHorizon.SWING,
    )

    assert rec_lt.trade_plan.tp1_pct > rec_swing.trade_plan.tp1_pct
    assert rec_lt.trade_plan.tp2_pct > rec_swing.trade_plan.tp2_pct
    assert rec_lt.trade_plan.risk_reward_ratio >= 1.5


def test_calculate_stock_shares_normal():
    # $10,000 cash, 2% risk ($200), $100 entry, $95 stop ($5 risk/share) -> 40 shares
    result = calculate_stock_shares(
        cash=10000.0,
        risk_pct=2.0,
        entry_price=100.0,
        stop_loss=95.0,
    )

    assert isinstance(result, dict)
    assert result["shares"] == 40
    assert result["capital_required"] == 4000.0
    assert result["risk_amount"] == 200.0
    assert result["risk_per_share"] == 5.0
    assert result["max_loss"] == 200.0


def test_calculate_stock_shares_zero_risk_fallback():
    # Invalid stop loss equal to entry (risk per share = 0)
    res_zero = calculate_stock_shares(
        cash=10000.0,
        risk_pct=2.0,
        entry_price=100.0,
        stop_loss=100.0,
    )
    assert res_zero["shares"] == 0
    assert res_zero["capital_required"] == 0.0

    # Stop loss higher than entry (invalid for long trade)
    res_inv = calculate_stock_shares(
        cash=10000.0,
        risk_pct=2.0,
        entry_price=100.0,
        stop_loss=105.0,
    )
    assert res_inv["shares"] == 0

    # Stop loss is zero or negative
    res_neg = calculate_stock_shares(
        cash=10000.0,
        risk_pct=2.0,
        entry_price=100.0,
        stop_loss=0.0,
    )
    assert res_neg["shares"] == 0

    # Zero cash or zero entry price
    res_no_cash = calculate_stock_shares(
        cash=0.0,
        risk_pct=2.0,
        entry_price=100.0,
        stop_loss=95.0,
    )
    assert res_no_cash["shares"] == 0


def test_stock_recommendation_with_dict_quote():
    quote_dict = {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "current_price": 220.0,
        "previous_close": 218.0,
        "valid": True,
    }
    momentum = _make_dummy_momentum(symbol="AAPL", last_close=220.0)

    rec = generate_stock_recommendation(quote=quote_dict, momentum=momentum)
    assert rec.symbol == "AAPL"
    assert rec.trade_plan.current_price == 220.0
    assert rec.trade_plan.risk_reward_ratio >= 1.5
    assert len(rec.rationale) > 0


def test_stock_selection_institutional_metrics():
    # Construct a historical dataframe with an upward trend
    dates = pd.date_range("2024-01-01", periods=60, freq="B")
    prices = [100.0 + i * 1.5 for i in range(60)]
    df = pd.DataFrame({
        "Open": prices,
        "High": [p + 2.0 for p in prices],
        "Low": [p - 1.0 for p in prices],
        "Close": prices,
        "Volume": [1000000] * 60,
    }, index=dates)

    momentum = _make_dummy_momentum(symbol="TSLA", last_close=float(prices[-1]), momentum_score=0.6)
    rec = generate_stock_recommendation(
        symbol="TSLA",
        momentum=momentum,
        df=df,
    )

    assert hasattr(rec, "relative_strength_score")
    assert 1.0 <= rec.relative_strength_score <= 99.0
    assert hasattr(rec, "distance_from_52w_high_pct")
    assert rec.distance_from_52w_high_pct <= 0.0
    assert hasattr(rec, "ma_alignment")
    assert hasattr(rec, "strategy_tag")
    assert rec.strategy_tag in (
        "STAGE_2_LEADER", "VCP_SQUEEZE", "INSTITUTIONAL_INFLOW",
        "RS_LEADER", "52W_BREAKOUT", "GOLDEN_CROSS", "PULLBACK_DIP", "VOLUME_SURGE", "MOMENTUM_SWING"
    )
    assert hasattr(rec, "is_stage_2")
    assert hasattr(rec, "is_vcp_squeeze")
    assert hasattr(rec, "consolidation_tightness")
    assert hasattr(rec, "accumulation_rating")
    assert hasattr(rec, "up_down_volume_ratio")


def test_evaluate_minervini_stage_2():
    # Strong Stage 2: Price > 50 SMA > 200 SMA, 200 SMA rising, near 52W high
    dates = pd.date_range("2023-01-01", periods=220, freq="B")
    prices = [50.0 + (i * 0.5) for i in range(220)]  # steadily rising from 50 to 159.5
    df_bull = pd.DataFrame({
        "Open": prices,
        "High": [p + 1.0 for p in prices],
        "Low": [p - 1.0 for p in prices],
        "Close": prices,
        "Volume": [1000000] * 220,
    }, index=dates)

    cur_p = float(prices[-1])
    is_s2 = evaluate_minervini_stage_2(
        df=df_bull,
        current_price=cur_p,
        fifty_two_week_high=cur_p * 1.02,
        fifty_two_week_low=50.0,
    )
    assert is_s2 is True

    # Failed Stage 2: Price below 50 SMA and 200 SMA
    is_s2_fail = evaluate_minervini_stage_2(
        df=df_bull,
        current_price=40.0,  # Below 200 SMA
        fifty_two_week_high=160.0,
        fifty_two_week_low=35.0,
    )
    assert is_s2_fail is False


def test_evaluate_vcp_squeeze():
    # Tight consolidation: range of last 10 days is narrow compared to previous 30 days
    dates = pd.date_range("2024-01-01", periods=40, freq="B")
    # First 30 days volatile: swings between 90 and 110
    prices_30 = [100.0 + (10.0 if i % 2 == 0 else -10.0) for i in range(30)]
    # Last 10 days tight consolidation around 100 with 0.5 variation
    prices_10 = [100.0 + (0.3 if i % 2 == 0 else -0.3) for i in range(10)]
    all_prices = prices_30 + prices_10

    df_squeeze = pd.DataFrame({
        "Open": all_prices,
        "High": [p + 0.5 for p in all_prices],
        "Low": [p - 0.5 for p in all_prices],
        "Close": all_prices,
        "Volume": [1000000] * 40,
    }, index=dates)

    is_squeeze, tightness = evaluate_vcp_squeeze(df=df_squeeze, current_price=100.0)
    assert tightness >= 60.0
    assert is_squeeze is True


def test_evaluate_accumulation_distribution():
    dates = pd.date_range("2024-01-01", periods=20, freq="B")
    # Up days have massive volume, down days have minimal volume
    closes = []
    volumes = []
    p = 100.0
    for i in range(20):
        if i % 2 == 0:
            p += 2.0  # Up day
            closes.append(p)
            volumes.append(5000000)  # Huge institutional volume
        else:
            p -= 0.5  # Small down day
            closes.append(p)
            volumes.append(500000)  # Light volume

    df_accum = pd.DataFrame({
        "Close": closes,
        "Volume": volumes,
    }, index=dates)

    rating_up, ratio_up = evaluate_accumulation_distribution(df=df_accum)
    assert rating_up in ("A+", "A")
    assert ratio_up >= 1.5

    # Reverse: Down days have massive volume (distribution)
    volumes_dist = [500000 if i % 2 == 0 else 5000000 for i in range(20)]
    df_dist = pd.DataFrame({
        "Close": closes,
        "Volume": volumes_dist,
    }, index=dates)

    rating_down, ratio_down = evaluate_accumulation_distribution(df=df_dist)
    assert rating_down in ("D", "C")
    assert ratio_down < 0.75


def test_screener_cache_institutional_filtering_and_sorting():
    cache = StockScreenerCache(seed_defaults=True)

    # Strategy filter: stage_2
    s2_res = cache.get_recommendations(strategy="stage_2")
    assert s2_res["total"] > 0
    for it in s2_res["items"]:
        assert it.get("is_stage_2") is True or it.get("strategy_tag") == "STAGE_2_LEADER"

    # Strategy filter: vcp_squeeze
    vcp_res = cache.get_recommendations(strategy="vcp_squeeze")
    assert vcp_res["total"] > 0
    for it in vcp_res["items"]:
        assert it.get("is_vcp_squeeze") is True or it.get("strategy_tag") == "VCP_SQUEEZE" or it.get("consolidation_tightness", 0) >= 65.0

    # Strategy filter: accumulation
    accum_res = cache.get_recommendations(strategy="accumulation")
    assert accum_res["total"] > 0
    for it in accum_res["items"]:
        assert it.get("accumulation_rating") in ("A+", "A") or it.get("strategy_tag") == "INSTITUTIONAL_INFLOW" or it.get("up_down_volume_ratio", 0) >= 1.25

    # Sort by: stage_2
    sorted_s2 = cache.get_recommendations(sort_by="stage_2")
    assert sorted_s2["items"][0].get("is_stage_2") is True

    # Sort by: accumulation (up_down_volume_ratio desc)
    sorted_accum = cache.get_recommendations(sort_by="accumulation")
    ratios = [it.get("up_down_volume_ratio", 1.0) for it in sorted_accum["items"]]
    assert ratios == sorted(ratios, reverse=True)

    # Sort by: vcp (consolidation_tightness desc)
    sorted_vcp = cache.get_recommendations(sort_by="vcp")
    tightness_list = [it.get("consolidation_tightness", 50.0) for it in sorted_vcp["items"]]
    assert tightness_list == sorted(tightness_list, reverse=True)


def test_analysis_package_level_exports():
    import analysis
    assert hasattr(analysis, "TradeHorizon")
    assert hasattr(analysis, "StockTradePlan")
    assert hasattr(analysis, "StockRecommendation")
    assert hasattr(analysis, "generate_stock_recommendation")
    assert hasattr(analysis, "calculate_stock_shares")
