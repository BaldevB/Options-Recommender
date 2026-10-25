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
)


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


def test_analysis_package_level_exports():
    import analysis
    assert hasattr(analysis, "TradeHorizon")
    assert hasattr(analysis, "StockTradePlan")
    assert hasattr(analysis, "StockRecommendation")
    assert hasattr(analysis, "generate_stock_recommendation")
    assert hasattr(analysis, "calculate_stock_shares")
