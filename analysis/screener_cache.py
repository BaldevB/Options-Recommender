"""High-speed in-memory Screener Cache & Intraday Background Refresh Manager.

Maintains thread-safe pre-computed stock recommendations across 1,000+ US equities,
supporting sub-second multi-parameter filtering (horizon, sector, search, strategy),
multi-column sorting, pagination, on-demand deep-dive analysis, and background batch refreshes.
"""

from dataclasses import asdict
from datetime import datetime, timezone
import logging
import threading
import time
from typing import Dict, List, Any, Optional, Union

import pandas as pd
import yfinance as yf

from analysis.momentum import analyze_momentum
from analysis.stock_suggester import (
    TradeHorizon,
    StockRecommendation,
    generate_stock_recommendation,
)
from data.stock_universe import get_stock_universe, STOCK_SECTORS

logger = logging.getLogger(__name__)

PRIORITY_LEADER_TICKERS = [
    "NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "AMD",
    "PLTR", "AVGO", "CRWD", "SMCI", "CCJ", "FCX", "XOM", "JPM",
    "LLY", "COST", "WMT", "NFLX", "ARM", "PANW", "COIN", "MU",
    "INTC", "MRVL", "QCOM", "NOW", "ISRG", "UBER", "CAT", "GE",
    "V", "MA", "UNH", "ABBV", "CVX", "SLB", "NUE", "URA",
]


def normalize_sector_query(sector: Optional[str]) -> Optional[str]:
    """Normalize user or internal sector string to standard lowercase slug."""
    if not sector or sector.strip().lower() in ("all", ""):
        return None
    s = sector.strip().lower().replace(" ", "_").replace("&", "and")
    alias_map = {
        "information_technology": "technology",
        "tech": "technology",
        "health_care": "healthcare",
        "health": "healthcare",
        "financial": "financials",
        "finance": "financials",
        "discretionary": "consumer_discretionary",
        "staples": "consumer_staples",
        "communication": "communication_services",
        "comms": "communication_services",
        "telecom": "communication_services",
        "industrial": "industrials",
        "material": "materials",
        "utility": "utilities",
        "reit": "real_estate",
        "reits": "real_estate",
        "ai": "ai_specialty",
        "ai_and_specialty": "ai_specialty",
        "specialty": "ai_specialty",
    }
    return alias_map.get(s, s)


def recommendation_to_dict(
    rec: Union[StockRecommendation, Dict[str, Any]],
    momentum: Optional[Any] = None,
    quote: Optional[Any] = None,
) -> Dict[str, Any]:
    """Convert a StockRecommendation dataclass or dictionary to a uniform JSON-ready dict."""
    if isinstance(rec, dict):
        d = dict(rec)
        if "trade_plan" in d and hasattr(d["trade_plan"], "__dict__"):
            d["trade_plan"] = asdict(d["trade_plan"])
        if hasattr(d.get("horizon"), "value"):
            d["horizon"] = d["horizon"].value
        if "price" not in d and "trade_plan" in d and isinstance(d["trade_plan"], dict):
            d["price"] = d["trade_plan"].get("current_price", 0.0)
        if "target_pct" not in d and "trade_plan" in d and isinstance(d["trade_plan"], dict):
            d["target_pct"] = d["trade_plan"].get("tp1_pct", 0.0)
        if "relative_strength_score" not in d:
            d["relative_strength_score"] = float(d.get("relative_strength", 50.0))
        if "distance_from_52w_high_pct" not in d:
            d["distance_from_52w_high_pct"] = float(d.get("dist_52w_pct", 0.0))
        if "ma_alignment" not in d:
            d["ma_alignment"] = str(d.get("ma_structure", "NEUTRAL"))
        if "strategy_tag" not in d:
            d["strategy_tag"] = str(d.get("strategy", "MOMENTUM_SWING"))
        if "is_stage_2" not in d:
            d["is_stage_2"] = bool(d.get("is_stage_2", False))
        if "is_vcp_squeeze" not in d:
            d["is_vcp_squeeze"] = bool(d.get("is_vcp_squeeze", False))
        if "consolidation_tightness" not in d:
            d["consolidation_tightness"] = float(d.get("consolidation_tightness", 50.0))
        if "accumulation_rating" not in d:
            d["accumulation_rating"] = str(d.get("accumulation_rating", "B"))
        if "up_down_volume_ratio" not in d:
            d["up_down_volume_ratio"] = float(d.get("up_down_volume_ratio", 1.0))
        return d

    plan = rec.trade_plan
    plan_dict = {
        "entry_zone": list(plan.entry_zone),
        "current_price": round(float(plan.current_price), 2),
        "tp1": round(float(plan.tp1), 2),
        "tp2": round(float(plan.tp2), 2),
        "stop_loss": round(float(plan.stop_loss), 2),
        "risk_reward_ratio": round(float(plan.risk_reward_ratio), 2),
        "invalidation_pct": round(float(plan.invalidation_pct), 2),
        "tp1_pct": round(float(plan.tp1_pct), 2),
        "tp2_pct": round(float(plan.tp2_pct), 2),
    }

    current_price = plan.current_price
    change = 0.0
    change_pct = 0.0
    volume_ratio = getattr(momentum, "volume_ratio", 1.0) if momentum else 1.0
    rsi = getattr(momentum, "rsi", 50.0) if momentum else 50.0

    if quote:
        if isinstance(quote, dict):
            change = float(quote.get("change", 0.0))
            change_pct = float(quote.get("change_percent", 0.0))
        elif hasattr(quote, "change"):
            change = float(getattr(quote, "change", 0.0))
            change_pct = float(getattr(quote, "change_percent", 0.0))

    horizon_val = rec.horizon.value if hasattr(rec.horizon, "value") else str(rec.horizon)

    rs_score = getattr(rec, "relative_strength_score", 50.0)
    dist_52w = getattr(rec, "distance_from_52w_high_pct", 0.0)
    ma_align = getattr(rec, "ma_alignment", "NEUTRAL")
    strat = getattr(rec, "strategy_tag", "MOMENTUM_SWING")
    is_stage_2 = getattr(rec, "is_stage_2", False)
    is_vcp = getattr(rec, "is_vcp_squeeze", False)
    tightness = getattr(rec, "consolidation_tightness", 50.0)
    accum_rating = getattr(rec, "accumulation_rating", "B")
    up_down_ratio = getattr(rec, "up_down_volume_ratio", 1.0)

    return {
        "symbol": rec.symbol,
        "name": rec.name,
        "sector": rec.sector,
        "horizon": horizon_val,
        "action": rec.action,
        "score": round(float(rec.score), 1),
        "confidence": round(float(rec.confidence), 2),
        "momentum_score": round(float(rec.momentum_score), 2),
        "sentiment_score": round(float(rec.sentiment_score), 2),
        "trade_plan": plan_dict,
        "rationale": list(rec.rationale),
        "price": current_price,
        "change": round(change, 2),
        "change_pct": round(change_pct, 2),
        "volume_ratio": round(volume_ratio, 2),
        "rsi": round(rsi, 1),
        "target_pct": plan.tp1_pct,
        "relative_strength_score": round(float(rs_score), 1),
        "distance_from_52w_high_pct": round(float(dist_52w), 1),
        "ma_alignment": ma_align,
        "strategy_tag": strat,
        "is_stage_2": bool(is_stage_2),
        "is_vcp_squeeze": bool(is_vcp),
        "consolidation_tightness": round(float(tightness), 1),
        "accumulation_rating": str(accum_rating),
        "up_down_volume_ratio": round(float(up_down_ratio), 2),
    }


def _get_default_seed_stocks() -> List[Dict[str, Any]]:
    """Return an instant curated seed of recommendations across sectors and strategies."""
    return [
        {
            "symbol": "NVDA",
            "name": "NVIDIA Corporation",
            "sector": "technology",
            "horizon": "SWING",
            "action": "STRONG BUY",
            "score": 93.5,
            "confidence": 0.88,
            "momentum_score": 0.74,
            "sentiment_score": 0.45,
            "trade_plan": {
                "entry_zone": [138.0, 142.5],
                "current_price": 141.20,
                "tp1": 158.0,
                "tp2": 172.0,
                "stop_loss": 132.5,
                "risk_reward_ratio": 2.15,
                "invalidation_pct": 6.16,
                "tp1_pct": 11.9,
                "tp2_pct": 21.8,
            },
            "rationale": [
                "Dominant institutional demand and high RS percentile rating (94) vs market benchmark.",
                "Minervini Stage 2 Confirmed: Full uptrend template with price > 50 DMA > 200 DMA.",
                "Institutional Flow: A+ Rating (Up/Down Volume Ratio: 1.85x).",
                "Consolidating inside high-probability breakout zone within 2% of 52-week rolling highs.",
            ],
            "price": 141.20,
            "change": 3.45,
            "change_pct": 2.51,
            "volume_ratio": 1.45,
            "rsi": 64.2,
            "target_pct": 11.9,
            "relative_strength_score": 94.0,
            "distance_from_52w_high_pct": -1.8,
            "ma_alignment": "FULL_BULLISH",
            "strategy_tag": "STAGE_2_LEADER",
            "is_stage_2": True,
            "is_vcp_squeeze": False,
            "consolidation_tightness": 74.0,
            "accumulation_rating": "A+",
            "up_down_volume_ratio": 1.85,
        },
        {
            "symbol": "PLTR",
            "name": "Palantir Technologies Inc.",
            "sector": "technology",
            "horizon": "SWING",
            "action": "STRONG BUY",
            "score": 94.0,
            "confidence": 0.90,
            "momentum_score": 0.82,
            "sentiment_score": 0.40,
            "trade_plan": {
                "entry_zone": [42.8, 44.2],
                "current_price": 43.75,
                "tp1": 50.0,
                "tp2": 56.0,
                "stop_loss": 40.5,
                "risk_reward_ratio": 2.25,
                "invalidation_pct": 7.43,
                "tp1_pct": 14.3,
                "tp2_pct": 28.0,
            },
            "rationale": [
                "Top 1% market leader with Relative Strength of 97 and high volume accumulation.",
                "Minervini Stage 2 Confirmed: Full uptrend template with price > 50 DMA > 200 DMA.",
                "VCP Squeeze Active: Volatility compression tightness score of 88/100.",
                "Institutional Flow: A+ Rating (Up/Down Volume Ratio: 2.10x).",
            ],
            "price": 43.75,
            "change": 1.85,
            "change_pct": 4.42,
            "volume_ratio": 1.72,
            "rsi": 68.5,
            "target_pct": 14.3,
            "relative_strength_score": 97.0,
            "distance_from_52w_high_pct": -0.6,
            "ma_alignment": "FULL_BULLISH",
            "strategy_tag": "STAGE_2_LEADER",
            "is_stage_2": True,
            "is_vcp_squeeze": True,
            "consolidation_tightness": 88.0,
            "accumulation_rating": "A+",
            "up_down_volume_ratio": 2.10,
        },
        {
            "symbol": "TSLA",
            "name": "Tesla, Inc.",
            "sector": "consumer_discretionary",
            "horizon": "SWING",
            "action": "STRONG BUY",
            "score": 91.0,
            "confidence": 0.84,
            "momentum_score": 0.70,
            "sentiment_score": 0.35,
            "trade_plan": {
                "entry_zone": [255.0, 264.0],
                "current_price": 260.50,
                "tp1": 295.0,
                "tp2": 320.0,
                "stop_loss": 242.0,
                "risk_reward_ratio": 2.10,
                "invalidation_pct": 7.10,
                "tp1_pct": 13.2,
                "tp2_pct": 22.8,
            },
            "rationale": [
                "Strong relative strength vs broader market with sharp upward momentum surge.",
                "Minervini Stage 2 Confirmed: Price > 50 DMA > 200 DMA.",
                "Institutional Flow: A+ Rating (Up/Down Volume Ratio: 1.65x).",
            ],
            "price": 260.50,
            "change": 7.30,
            "change_pct": 2.88,
            "volume_ratio": 1.38,
            "rsi": 62.0,
            "target_pct": 13.2,
            "relative_strength_score": 91.0,
            "distance_from_52w_high_pct": -2.4,
            "ma_alignment": "FULL_BULLISH",
            "strategy_tag": "STAGE_2_LEADER",
            "is_stage_2": True,
            "is_vcp_squeeze": False,
            "consolidation_tightness": 68.0,
            "accumulation_rating": "A+",
            "up_down_volume_ratio": 1.65,
        },
        {
            "symbol": "META",
            "name": "Meta Platforms, Inc.",
            "sector": "communication_services",
            "horizon": "SWING",
            "action": "STRONG BUY",
            "score": 90.5,
            "confidence": 0.86,
            "momentum_score": 0.68,
            "sentiment_score": 0.38,
            "trade_plan": {
                "entry_zone": [575.0, 588.0],
                "current_price": 582.00,
                "tp1": 640.0,
                "tp2": 690.0,
                "stop_loss": 552.0,
                "risk_reward_ratio": 2.12,
                "invalidation_pct": 5.15,
                "tp1_pct": 10.0,
                "tp2_pct": 18.6,
            },
            "rationale": [
                "Testing all-time rolling highs with steady accumulation from institutional funds.",
                "VCP Squeeze Active: Volatility compression tightness score of 84/100.",
                "Institutional Flow: A+ Rating (Up/Down Volume Ratio: 1.58x).",
            ],
            "price": 582.00,
            "change": 8.50,
            "change_pct": 1.48,
            "volume_ratio": 1.25,
            "rsi": 63.5,
            "target_pct": 10.0,
            "relative_strength_score": 92.0,
            "distance_from_52w_high_pct": -1.2,
            "ma_alignment": "FULL_BULLISH",
            "strategy_tag": "INSTITUTIONAL_INFLOW",
            "is_stage_2": True,
            "is_vcp_squeeze": True,
            "consolidation_tightness": 84.0,
            "accumulation_rating": "A+",
            "up_down_volume_ratio": 1.58,
        },
        {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "sector": "technology",
            "horizon": "LONG_TERM",
            "action": "BUY ACCUMULATE",
            "score": 84.5,
            "confidence": 0.82,
            "momentum_score": 0.52,
            "sentiment_score": 0.28,
            "trade_plan": {
                "entry_zone": [226.0, 232.0],
                "current_price": 229.50,
                "tp1": 252.0,
                "tp2": 270.0,
                "stop_loss": 218.0,
                "risk_reward_ratio": 1.95,
                "invalidation_pct": 5.01,
                "tp1_pct": 9.8,
                "tp2_pct": 17.6,
            },
            "rationale": [
                "VCP Squeeze Active: Tight volatility contraction holding the 50-day moving average.",
                "Healthy risk-reward ratio of 1.95:1 with manageable downside invalidation.",
                "Institutional Flow: A Rating (Up/Down Volume Ratio: 1.35x).",
            ],
            "price": 229.50,
            "change": 1.80,
            "change_pct": 0.79,
            "volume_ratio": 1.05,
            "rsi": 58.2,
            "target_pct": 9.8,
            "relative_strength_score": 82.0,
            "distance_from_52w_high_pct": -2.8,
            "ma_alignment": "BULLISH_TREND",
            "strategy_tag": "VCP_SQUEEZE",
            "is_stage_2": True,
            "is_vcp_squeeze": True,
            "consolidation_tightness": 82.0,
            "accumulation_rating": "A",
            "up_down_volume_ratio": 1.35,
        },
        {
            "symbol": "MSFT",
            "name": "Microsoft Corporation",
            "sector": "technology",
            "horizon": "SWING",
            "action": "BUY ACCUMULATE",
            "score": 86.0,
            "confidence": 0.83,
            "momentum_score": 0.58,
            "sentiment_score": 0.32,
            "trade_plan": {
                "entry_zone": [422.0, 430.0],
                "current_price": 426.00,
                "tp1": 465.0,
                "tp2": 490.0,
                "stop_loss": 405.0,
                "risk_reward_ratio": 1.86,
                "invalidation_pct": 4.93,
                "tp1_pct": 9.2,
                "tp2_pct": 15.0,
            },
            "rationale": [
                "Golden Cross formation with 50 SMA crossing above 200 SMA.",
                "Minervini Stage 2 Confirmed: Price > 50 DMA > 200 DMA.",
                "Institutional accumulation at key support zone (A Rating).",
            ],
            "price": 426.00,
            "change": 2.40,
            "change_pct": 0.57,
            "volume_ratio": 1.12,
            "rsi": 56.4,
            "target_pct": 9.2,
            "relative_strength_score": 85.0,
            "distance_from_52w_high_pct": -3.5,
            "ma_alignment": "GOLDEN_CROSS",
            "strategy_tag": "GOLDEN_CROSS",
            "is_stage_2": True,
            "is_vcp_squeeze": False,
            "consolidation_tightness": 62.0,
            "accumulation_rating": "A",
            "up_down_volume_ratio": 1.28,
        },
        {
            "symbol": "AMZN",
            "name": "Amazon.com, Inc.",
            "sector": "consumer_discretionary",
            "horizon": "SWING",
            "action": "STRONG BUY",
            "score": 89.0,
            "confidence": 0.85,
            "momentum_score": 0.65,
            "sentiment_score": 0.36,
            "trade_plan": {
                "entry_zone": [185.0, 190.0],
                "current_price": 188.50,
                "tp1": 210.0,
                "tp2": 225.0,
                "stop_loss": 178.0,
                "risk_reward_ratio": 2.05,
                "invalidation_pct": 5.57,
                "tp1_pct": 11.4,
                "tp2_pct": 19.4,
            },
            "rationale": [
                "Institutional Flow: A+ Rating (Up/Down Volume Ratio: 1.62x).",
                "Approaching 52-week rolling high with accelerating cloud margin expansion.",
                "VCP Squeeze Active: Tight volatility compression.",
            ],
            "price": 188.50,
            "change": 3.10,
            "change_pct": 1.67,
            "volume_ratio": 1.28,
            "rsi": 61.8,
            "target_pct": 11.4,
            "relative_strength_score": 88.0,
            "distance_from_52w_high_pct": -2.5,
            "ma_alignment": "GOLDEN_CROSS",
            "strategy_tag": "INSTITUTIONAL_INFLOW",
            "is_stage_2": True,
            "is_vcp_squeeze": True,
            "consolidation_tightness": 85.0,
            "accumulation_rating": "A+",
            "up_down_volume_ratio": 1.62,
        },
        {
            "symbol": "CCJ",
            "name": "Cameco Corporation",
            "sector": "energy",
            "horizon": "SWING",
            "action": "STRONG BUY",
            "score": 88.5,
            "confidence": 0.86,
            "momentum_score": 0.72,
            "sentiment_score": 0.42,
            "trade_plan": {
                "entry_zone": [52.0, 54.5],
                "current_price": 53.80,
                "tp1": 62.0,
                "tp2": 68.0,
                "stop_loss": 49.5,
                "risk_reward_ratio": 2.12,
                "invalidation_pct": 7.99,
                "tp1_pct": 15.2,
                "tp2_pct": 26.4,
            },
            "rationale": [
                "Nuclear energy & uranium secular multi-year structural supply deficit.",
                "Minervini Stage 2 Confirmed: Price > 50 DMA > 200 DMA.",
                "Institutional Flow: A+ Rating (Up/Down Volume Ratio: 1.75x).",
            ],
            "price": 53.80,
            "change": 1.95,
            "change_pct": 3.76,
            "volume_ratio": 1.48,
            "rsi": 66.0,
            "target_pct": 15.2,
            "relative_strength_score": 89.0,
            "distance_from_52w_high_pct": -1.9,
            "ma_alignment": "FULL_BULLISH",
            "strategy_tag": "52W_BREAKOUT",
            "is_stage_2": True,
            "is_vcp_squeeze": False,
            "consolidation_tightness": 70.0,
            "accumulation_rating": "A+",
            "up_down_volume_ratio": 1.75,
        },
        {
            "symbol": "FCX",
            "name": "Freeport-McMoRan Inc.",
            "sector": "materials",
            "horizon": "SWING",
            "action": "BUY ACCUMULATE",
            "score": 81.0,
            "confidence": 0.80,
            "momentum_score": 0.48,
            "sentiment_score": 0.25,
            "trade_plan": {
                "entry_zone": [44.0, 46.0],
                "current_price": 45.20,
                "tp1": 52.0,
                "tp2": 57.0,
                "stop_loss": 41.5,
                "risk_reward_ratio": 1.84,
                "invalidation_pct": 8.19,
                "tp1_pct": 15.0,
                "tp2_pct": 26.1,
            },
            "rationale": [
                "Pullback dip buy opportunity holding key support near the 50-day moving average.",
                "Copper demand fundamentals supported by AI data centers and electrification.",
                "Balanced volume accumulation (B Rating).",
            ],
            "price": 45.20,
            "change": 0.85,
            "change_pct": 1.92,
            "volume_ratio": 1.15,
            "rsi": 44.5,
            "target_pct": 15.0,
            "relative_strength_score": 78.0,
            "distance_from_52w_high_pct": -8.5,
            "ma_alignment": "ABOVE_50DMA",
            "strategy_tag": "PULLBACK_DIP",
            "is_stage_2": False,
            "is_vcp_squeeze": False,
            "consolidation_tightness": 54.0,
            "accumulation_rating": "B",
            "up_down_volume_ratio": 1.08,
        },
        {
            "symbol": "AMD",
            "name": "Advanced Micro Devices, Inc.",
            "sector": "technology",
            "horizon": "SWING",
            "action": "BUY ACCUMULATE",
            "score": 79.5,
            "confidence": 0.79,
            "momentum_score": 0.42,
            "sentiment_score": 0.22,
            "trade_plan": {
                "entry_zone": [148.0, 154.0],
                "current_price": 152.00,
                "tp1": 175.0,
                "tp2": 190.0,
                "stop_loss": 140.0,
                "risk_reward_ratio": 1.92,
                "invalidation_pct": 7.89,
                "tp1_pct": 15.1,
                "tp2_pct": 25.0,
            },
            "rationale": [
                "Pullback into strong horizontal support cluster with oversold RSI bounce.",
                "VCP Squeeze Active: Volatility compression tightness score of 78/100.",
                "Defined stop loss beneath the 200-day moving average zone.",
            ],
            "price": 152.00,
            "change": -1.20,
            "change_pct": -0.78,
            "volume_ratio": 1.10,
            "rsi": 42.0,
            "target_pct": 15.1,
            "relative_strength_score": 74.0,
            "distance_from_52w_high_pct": -14.2,
            "ma_alignment": "ABOVE_50DMA",
            "strategy_tag": "PULLBACK_DIP",
            "is_stage_2": False,
            "is_vcp_squeeze": True,
            "consolidation_tightness": 78.0,
            "accumulation_rating": "B",
            "up_down_volume_ratio": 0.98,
        },
        {
            "symbol": "JPM",
            "name": "JPMorgan Chase & Co.",
            "sector": "financials",
            "horizon": "LONG_TERM",
            "action": "STRONG BUY",
            "score": 87.0,
            "confidence": 0.85,
            "momentum_score": 0.60,
            "sentiment_score": 0.30,
            "trade_plan": {
                "entry_zone": [218.0, 224.0],
                "current_price": 222.00,
                "tp1": 245.0,
                "tp2": 260.0,
                "stop_loss": 210.0,
                "risk_reward_ratio": 1.92,
                "invalidation_pct": 5.41,
                "tp1_pct": 10.4,
                "tp2_pct": 17.1,
            },
            "rationale": [
                "Best-in-class financial franchise breaking out to new rolling highs.",
                "Minervini Stage 2 Confirmed: Price > 50 DMA > 200 DMA.",
                "Institutional Flow: A Rating (Up/Down Volume Ratio: 1.32x).",
            ],
            "price": 222.00,
            "change": 2.10,
            "change_pct": 0.96,
            "volume_ratio": 1.18,
            "rsi": 62.5,
            "target_pct": 10.4,
            "relative_strength_score": 86.0,
            "distance_from_52w_high_pct": -1.5,
            "ma_alignment": "FULL_BULLISH",
            "strategy_tag": "52W_BREAKOUT",
            "is_stage_2": True,
            "is_vcp_squeeze": False,
            "consolidation_tightness": 65.0,
            "accumulation_rating": "A",
            "up_down_volume_ratio": 1.32,
        },
        {
            "symbol": "LLY",
            "name": "Eli Lilly and Company",
            "sector": "healthcare",
            "horizon": "LONG_TERM",
            "action": "STRONG BUY",
            "score": 90.0,
            "confidence": 0.87,
            "momentum_score": 0.68,
            "sentiment_score": 0.35,
            "trade_plan": {
                "entry_zone": [890.0, 915.0],
                "current_price": 905.00,
                "tp1": 1020.0,
                "tp2": 1100.0,
                "stop_loss": 845.0,
                "risk_reward_ratio": 1.92,
                "invalidation_pct": 6.63,
                "tp1_pct": 12.7,
                "tp2_pct": 21.5,
            },
            "rationale": [
                "Healthcare sector market leader with RS rating of 90 and explosive GLP-1 revenue.",
                "Minervini Stage 2 Confirmed: Price > 50 DMA > 200 DMA.",
                "VCP Squeeze Active: Volatility compression tightness score of 87/100.",
                "Institutional Flow: A+ Rating (Up/Down Volume Ratio: 1.92x).",
            ],
            "price": 905.00,
            "change": 12.40,
            "change_pct": 1.39,
            "volume_ratio": 1.22,
            "rsi": 63.8,
            "target_pct": 12.7,
            "relative_strength_score": 90.0,
            "distance_from_52w_high_pct": -2.2,
            "ma_alignment": "FULL_BULLISH",
            "strategy_tag": "STAGE_2_LEADER",
            "is_stage_2": True,
            "is_vcp_squeeze": True,
            "consolidation_tightness": 87.0,
            "accumulation_rating": "A+",
            "up_down_volume_ratio": 1.92,
        },
        {
            "symbol": "COST",
            "name": "Costco Wholesale Corporation",
            "sector": "consumer_staples",
            "horizon": "LONG_TERM",
            "action": "STRONG BUY",
            "score": 88.0,
            "confidence": 0.86,
            "momentum_score": 0.62,
            "sentiment_score": 0.32,
            "trade_plan": {
                "entry_zone": [895.0, 920.0],
                "current_price": 912.00,
                "tp1": 1010.0,
                "tp2": 1080.0,
                "stop_loss": 860.0,
                "risk_reward_ratio": 1.88,
                "invalidation_pct": 5.70,
                "tp1_pct": 10.7,
                "tp2_pct": 18.4,
            },
            "rationale": [
                "Exceptional customer renewal rates and steady compound growth.",
                "Minervini Stage 2 Confirmed: Price > 50 DMA > 200 DMA.",
                "VCP Squeeze Active: Volatility compression tightness score of 83/100.",
            ],
            "price": 912.00,
            "change": 8.00,
            "change_pct": 0.88,
            "volume_ratio": 1.15,
            "rsi": 64.0,
            "target_pct": 10.7,
            "relative_strength_score": 87.0,
            "distance_from_52w_high_pct": -1.3,
            "ma_alignment": "FULL_BULLISH",
            "strategy_tag": "52W_BREAKOUT",
            "is_stage_2": True,
            "is_vcp_squeeze": True,
            "consolidation_tightness": 83.0,
            "accumulation_rating": "A",
            "up_down_volume_ratio": 1.40,
        },
        {
            "symbol": "CRWD",
            "name": "CrowdStrike Holdings, Inc.",
            "sector": "technology",
            "horizon": "SWING",
            "action": "STRONG BUY",
            "score": 86.5,
            "confidence": 0.84,
            "momentum_score": 0.64,
            "sentiment_score": 0.30,
            "trade_plan": {
                "entry_zone": [315.0, 325.0],
                "current_price": 322.00,
                "tp1": 365.0,
                "tp2": 395.0,
                "stop_loss": 298.0,
                "risk_reward_ratio": 1.79,
                "invalidation_pct": 7.45,
                "tp1_pct": 13.4,
                "tp2_pct": 22.7,
            },
            "rationale": [
                "Completed major bottoming base and reclaiming the 200-day moving average.",
                "Minervini Stage 2 Confirmed: Price > 50 DMA > 200 DMA.",
                "VCP Squeeze Active: Tight volatility contraction (81/100).",
                "Institutional Flow: A+ Rating (Up/Down Volume Ratio: 1.55x).",
            ],
            "price": 322.00,
            "change": 5.60,
            "change_pct": 1.77,
            "volume_ratio": 1.34,
            "rsi": 61.2,
            "target_pct": 13.4,
            "relative_strength_score": 84.0,
            "distance_from_52w_high_pct": -5.1,
            "ma_alignment": "GOLDEN_CROSS",
            "strategy_tag": "VCP_SQUEEZE",
            "is_stage_2": True,
            "is_vcp_squeeze": True,
            "consolidation_tightness": 81.0,
            "accumulation_rating": "A+",
            "up_down_volume_ratio": 1.55,
        },
    ]


def fetch_single_stock_analysis(symbol: str) -> Optional[Dict[str, Any]]:
    """Fetch on-demand deep dive stock analysis for any US equity symbol."""
    try:
        from data.price_data import get_current_quote, get_price_history, get_earnings_info
        from data.news_data import get_company_news
        from analysis.sentiment import analyze_news_sentiment

        symbol = symbol.strip().upper()
        quote = get_current_quote(symbol)
        if not quote.get("valid") and float(quote.get("current_price", 0.0)) <= 0:
            return None

        hist = get_price_history(symbol, period="6mo")
        momentum = None
        if hist is not None and not hist.empty and len(hist) >= 15:
            momentum = analyze_momentum(hist, symbol=symbol)

        sentiment = None
        try:
            articles = get_company_news(symbol, limit=5)
            sentiment = analyze_news_sentiment(articles, symbol=symbol)
        except Exception:
            pass

        earnings = None
        try:
            earnings = get_earnings_info(symbol)
        except Exception:
            pass

        rec = generate_stock_recommendation(
            symbol=symbol,
            quote=quote,
            momentum=momentum,
            sentiment=sentiment,
            df=hist,
            earnings_info=earnings,
        )
        return recommendation_to_dict(rec, momentum=momentum, quote=quote)
    except Exception as exc:
        logger.warning("Error fetching on-demand stock analysis for %s: %s", symbol, exc)
        return None


class StockScreenerCache:
    """Thread-safe in-memory cache and background refresh manager for stock screener."""

    def __init__(self, seed_defaults: bool = False) -> None:
        self._lock = threading.RLock()
        self._cached_items: List[Dict[str, Any]] = []
        self._cached_dict: Dict[str, Dict[str, Any]] = {}
        self._status: str = "empty"
        self._last_updated: Optional[str] = None
        self._last_updated_ts: Optional[float] = None
        self._next_refresh: Optional[str] = None
        self._is_refreshing: bool = False
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_worker_event: threading.Event = threading.Event()
        self._worker_interval_minutes: int = 15

        if seed_defaults:
            seeds = _get_default_seed_stocks()
            self._set_cached_items(seeds)

    def _set_cached_items(self, items: List[Union[StockRecommendation, Dict[str, Any]]]) -> None:
        """Helper to seed or overwrite cache thread-safely."""
        normalized = [recommendation_to_dict(it) for it in items]
        normalized.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self._cached_items = normalized
            self._cached_dict = {it["symbol"]: it for it in normalized}
            self._last_updated = now_iso
            self._last_updated_ts = time.time()
            self._status = "ready"

    def get_recommendations(
        self,
        horizon: Optional[str] = None,
        sector: Optional[str] = None,
        strategy: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "score",
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Query, filter, sort, and paginate cached stock recommendations in sub-second time.

        Args:
            horizon: Filter by timeframe horizon ('ALL', 'SWING', 'LONG_TERM', 'BREAKOUT').
            sector: Filter by sector slug or human-readable name.
            strategy: Preset strategy filter ('stage_2', 'vcp_squeeze', 'accumulation', 'rs_leaders', 'breakouts', 'golden_cross', 'pullback').
            search: Ticker symbol or company name search substring.
            sort_by: Sorting field ('score', 'symbol', 'price', 'change_pct', 'volume_ratio', 'rsi', 'stage_2', 'accumulation', 'vcp', etc.).
            limit: Page size limit (default 50).
            offset: Page offset (default 0).

        Returns:
            Dict containing total count, page items, pagination metadata, and updated timestamp.
        """
        with self._lock:
            if not self._cached_items and self._status == "empty":
                seeds = _get_default_seed_stocks()
                self._cached_items = [recommendation_to_dict(it) for it in seeds]
                self._cached_items.sort(key=lambda x: x.get("score", 0.0), reverse=True)
                self._cached_dict = {it["symbol"]: it for it in self._cached_items}
                self._last_updated = datetime.now(timezone.utc).isoformat()
                self._last_updated_ts = time.time()
                self._status = "ready"
            items_snapshot = list(self._cached_items)
            updated_at = self._last_updated

        filtered: List[Dict[str, Any]] = []

        # Parse horizon filter
        h_norm = horizon.strip().upper() if horizon else None
        if h_norm in ("ALL", "", "NONE"):
            h_norm = None

        # Parse sector filter
        s_norm = normalize_sector_query(sector)

        # Parse strategy filter
        strat_norm = strategy.strip().lower() if strategy else None
        if strat_norm in ("all", "", "none"):
            strat_norm = None

        # Parse search query
        q_norm = search.strip().lower() if search else None

        for item in items_snapshot:
            # 1. Horizon filter
            if h_norm is not None:
                if h_norm in ("BREAKOUT", "BREAKOUTS"):
                    vol = item.get("volume_ratio", 1.0)
                    act = item.get("action", "").upper()
                    mom = item.get("momentum_score", 0.0)
                    if not (vol >= 1.20 or ("BUY" in act and mom > 0.20)):
                        continue
                elif item.get("horizon", "").upper() != h_norm:
                    continue

            # 2. Sector filter
            if s_norm is not None:
                item_sec = normalize_sector_query(item.get("sector", ""))
                if item_sec != s_norm and item.get("sector", "").lower() != (sector or "").strip().lower():
                    continue

            # 3. Strategy filter
            if strat_norm is not None:
                tag = item.get("strategy_tag", "").lower()
                rs = item.get("relative_strength_score", 50.0)
                d52 = item.get("distance_from_52w_high_pct", -50.0)
                ma = item.get("ma_alignment", "").upper()
                rsi_val = item.get("rsi", 50.0)
                is_s2 = bool(item.get("is_stage_2", False))
                is_vcp = bool(item.get("is_vcp_squeeze", False))
                tightness_val = float(item.get("consolidation_tightness", 50.0))
                ad_rating = str(item.get("accumulation_rating", "B")).upper()
                ud_ratio = float(item.get("up_down_volume_ratio", 1.0))

                if strat_norm in ("stage_2", "stage2", "stage_2_leaders", "minervini"):
                    if not (is_s2 or tag == "stage_2_leader"):
                        continue
                elif strat_norm in ("vcp", "vcp_squeeze", "squeeze", "tightness"):
                    if not (is_vcp or tag == "vcp_squeeze" or tightness_val >= 65.0):
                        continue
                elif strat_norm in ("accumulation", "institutional_inflow", "inflow", "institutional"):
                    if not (ad_rating in ("A+", "A") or tag == "institutional_inflow" or ud_ratio >= 1.25):
                        continue
                elif strat_norm in ("rs_leaders", "rs", "relative_strength"):
                    if not (tag in ("rs_leader", "stage_2_leader") or rs >= 75.0):
                        continue
                elif strat_norm in ("breakouts", "52w_breakouts", "breakout"):
                    if not (tag == "52w_breakout" or d52 >= -7.0):
                        continue
                elif strat_norm in ("golden_cross", "golden"):
                    if not (tag == "golden_cross" or "GOLDEN" in ma or "FULL_BULLISH" in ma or "BULLISH" in ma):
                        continue
                elif strat_norm in ("pullback", "pullback_dips", "dip_buy", "dips"):
                    if not (tag == "pullback_dip" or rsi_val <= 45.0):
                        continue

            # 4. Search query
            if q_norm is not None:
                sym_match = q_norm in item.get("symbol", "").lower()
                name_match = q_norm in item.get("name", "").lower()
                if not (sym_match or name_match):
                    continue

            filtered.append(item)

        # Sorting
        sort_field = (sort_by or "score").strip().lower()
        if sort_field in ("score", "composite_score"):
            filtered.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        elif sort_field in ("symbol", "ticker"):
            filtered.sort(key=lambda x: x.get("symbol", ""))
        elif sort_field in ("price", "current_price"):
            filtered.sort(key=lambda x: x.get("price", 0.0), reverse=True)
        elif sort_field in ("change", "change_pct", "change_percent", "24h"):
            filtered.sort(key=lambda x: x.get("change_pct", 0.0), reverse=True)
        elif sort_field in ("volume_ratio", "vol_ratio", "volume"):
            filtered.sort(key=lambda x: x.get("volume_ratio", 1.0), reverse=True)
        elif sort_field in ("rsi",):
            filtered.sort(key=lambda x: x.get("rsi", 50.0), reverse=True)
        elif sort_field in ("confidence",):
            filtered.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)
        elif sort_field in ("risk_reward", "risk_reward_ratio", "rr"):
            filtered.sort(key=lambda x: x.get("trade_plan", {}).get("risk_reward_ratio", 1.5), reverse=True)
        elif sort_field in ("target_pct", "target", "tp1_pct"):
            filtered.sort(key=lambda x: x.get("target_pct", 0.0), reverse=True)
        elif sort_field in ("rs", "relative_strength", "alpha", "rs_score"):
            filtered.sort(key=lambda x: x.get("relative_strength_score", 50.0), reverse=True)
        elif sort_field in ("dist_52w", "distance_52w", "52w_high"):
            filtered.sort(key=lambda x: x.get("distance_from_52w_high_pct", -100.0), reverse=True)
        elif sort_field in ("stage_2", "stage2", "minervini"):
            filtered.sort(key=lambda x: (1 if x.get("is_stage_2") else 0, x.get("score", 0.0)), reverse=True)
        elif sort_field in ("accumulation", "inflow", "ad_ratio", "up_down_volume_ratio", "up_down_ratio"):
            filtered.sort(key=lambda x: x.get("up_down_volume_ratio", 1.0), reverse=True)
        elif sort_field in ("vcp", "vcp_squeeze", "tightness", "squeeze", "consolidation_tightness"):
            filtered.sort(key=lambda x: x.get("consolidation_tightness", 50.0), reverse=True)
        else:
            filtered.sort(key=lambda x: x.get("score", 0.0), reverse=True)

        total = len(filtered)
        start = max(0, offset)
        end = start + max(1, limit)
        paged_items = filtered[start:end]

        return {
            "total": total,
            "items": paged_items,
            "limit": limit,
            "offset": offset,
            "updated_at": updated_at,
        }

    def get_analysis(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Retrieve full deep dive analysis for a symbol from cache or on-demand scan."""
        sym = symbol.strip().upper()
        with self._lock:
            if sym in self._cached_dict:
                return dict(self._cached_dict[sym])

        # On-demand fallback
        analysis = fetch_single_stock_analysis(sym)
        if analysis:
            with self._lock:
                self._cached_dict[sym] = analysis
            return analysis
        return None

    def get_status(self) -> Dict[str, Any]:
        """Get screener cache status, counts, and background worker state."""
        with self._lock:
            return {
                "status": self._status,
                "cached_stocks": len(self._cached_items),
                "total_stocks": len(get_stock_universe()),
                "total_universe": len(get_stock_universe()),
                "is_refreshing": self._is_refreshing,
                "last_updated": self._last_updated,
                "next_refresh": self._next_refresh,
                "worker_running": self._worker_thread is not None and self._worker_thread.is_alive(),
            }

    def refresh_cache(
        self,
        force: bool = False,
        tickers: Optional[List[str]] = None,
        chunk_size: int = 100,
    ) -> Dict[str, Any]:
        """Perform batch historical price downloads, compute momentum & trade plans, and refresh cache.

        Progressively updates the cache after each batch chunk so recommendations
        appear immediately rather than waiting for the entire universe to finish.
        """
        with self._lock:
            if self._is_refreshing and not force:
                return {
                    "status": "already_refreshing",
                    "updated_at": self._last_updated,
                    "cached_stocks": len(self._cached_items),
                }
            self._is_refreshing = True
            if not self._cached_items:
                self._status = "refreshing"

        try:
            if tickers is None:
                universe_items = get_stock_universe()
                all_tickers = [item["symbol"] for item in universe_items]
                # Order priority market leaders first so they appear immediately
                priorities = [t for t in PRIORITY_LEADER_TICKERS if t in all_tickers]
                remaining = [t for t in all_tickers if t not in PRIORITY_LEADER_TICKERS]
                clean_tickers = priorities + remaining
            else:
                all_tickers = [t.strip().upper() for t in tickers if t and t.strip()]
                clean_tickers = list(dict.fromkeys(all_tickers))

            recs: List[Dict[str, Any]] = []

            for i in range(0, len(clean_tickers), chunk_size):
                chunk = clean_tickers[i : i + chunk_size]
                chunk_str = " ".join(chunk)

                try:
                    data = yf.download(
                        chunk_str,
                        period="3mo",
                        interval="1d",
                        group_by="ticker",
                        threads=True,
                        progress=False,
                    )
                except Exception as exc:
                    logger.warning("Error during batch download chunk [%s...]: %s", chunk[:3], exc)
                    continue

                if data is None or data.empty:
                    continue

                is_multi = isinstance(data.columns, pd.MultiIndex)
                level0_cols = set(data.columns.get_level_values(0)) if is_multi else set()
                level1_cols = set(data.columns.get_level_values(1)) if is_multi else set()

                chunk_recs: List[Dict[str, Any]] = []
                for sym in chunk:
                    try:
                        df_sym: Optional[pd.DataFrame] = None
                        if is_multi:
                            if sym in level0_cols:
                                df_sym = data[sym].dropna(subset=["Close"]).copy()
                            elif sym in level1_cols:
                                df_sym = data.xs(sym, axis=1, level=1).dropna(subset=["Close"]).copy()
                        else:
                            df_sym = data.dropna(subset=["Close"]).copy()

                        if df_sym is None or len(df_sym) < 15:
                            continue

                        # Compute momentum
                        mom = analyze_momentum(df_sym, symbol=sym)

                        # Determine price change
                        last_close = float(df_sym["Close"].iloc[-1])
                        prev_close = float(df_sym["Close"].iloc[-2]) if len(df_sym) > 1 else last_close
                        change = last_close - prev_close
                        change_percent = (change / prev_close) * 100.0 if prev_close > 0 else 0.0

                        quote_summary = {
                            "symbol": sym,
                            "current_price": round(last_close, 2),
                            "previous_close": round(prev_close, 2),
                            "change": round(change, 2),
                            "change_percent": round(change_percent, 2),
                            "day_high": float(df_sym["High"].iloc[-1]),
                            "day_low": float(df_sym["Low"].iloc[-1]),
                            "fifty_two_week_high": float(df_sym["High"].max()),
                            "fifty_two_week_low": float(df_sym["Low"].min()),
                            "volume": int(df_sym["Volume"].iloc[-1]),
                            "valid": True,
                        }

                        # Generate recommendation
                        rec = generate_stock_recommendation(
                            symbol=sym,
                            quote=quote_summary,
                            momentum=mom,
                            df=df_sym,
                        )

                        rec_dict = recommendation_to_dict(rec, momentum=mom, quote=quote_summary)
                        chunk_recs.append(rec_dict)
                        recs.append(rec_dict)
                    except Exception as sym_exc:
                        logger.debug("Skipping symbol %s due to computation error: %s", sym, sym_exc)
                        continue

                # Progressively update cache after each chunk (only when scanning full universe)
                if chunk_recs and tickers is None:
                    with self._lock:
                        for it in chunk_recs:
                            self._cached_dict[it["symbol"]] = it
                        self._cached_items = sorted(
                            self._cached_dict.values(),
                            key=lambda x: x.get("score", 0.0),
                            reverse=True,
                        )
                        self._last_updated = datetime.now(timezone.utc).isoformat()
                        self._last_updated_ts = time.time()
                        self._status = "ready"

            if recs:
                if tickers is not None:
                    self._set_cached_items(recs)
                logger.info("Stock screener cache refreshed successfully with %d stocks.", len(recs))
                return {
                    "status": "success",
                    "scanned_stocks": len(recs),
                    "updated_at": self._last_updated,
                }
            else:
                if tickers is not None:
                    with self._lock:
                        self._cached_items = []
                        self._cached_dict = {}
                        self._status = "empty"
                else:
                    with self._lock:
                        if not self._cached_items:
                            self._status = "empty"
                        else:
                            self._status = "ready"
                return {
                    "status": "empty",
                    "scanned_stocks": 0,
                    "updated_at": self._last_updated,
                }

        except Exception as exc:
            logger.error("Failed to refresh stock screener cache: %s", exc)
            with self._lock:
                self._status = "error" if not self._cached_items else "ready"
            return {
                "status": "error",
                "message": str(exc),
                "updated_at": self._last_updated,
            }
        finally:
            with self._lock:
                self._is_refreshing = False

    def start_background_worker(self, interval_minutes: int = 15) -> None:
        """Start daemon background worker thread to periodically refresh cache."""
        with self._lock:
            if self._worker_thread is not None and self._worker_thread.is_alive():
                return
            self._stop_worker_event.clear()
            self._worker_interval_minutes = interval_minutes
            self._worker_thread = threading.Thread(
                target=self._worker_loop,
                daemon=True,
                name="StockScreenerCacheWorker",
            )
            self._worker_thread.start()
            logger.info("Stock screener background worker started (interval=%dm).", interval_minutes)

    def stop_background_worker(self, timeout: float = 5.0) -> None:
        """Stop background worker thread."""
        self._stop_worker_event.set()
        if self._worker_thread is not None and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=timeout)
            self._worker_thread = None
            logger.info("Stock screener background worker stopped.")

    def _worker_loop(self) -> None:
        """Periodic background refresh worker loop."""
        while not self._stop_worker_event.is_set():
            try:
                self.refresh_cache()
            except Exception as exc:
                logger.error("Error in screener cache background refresh: %s", exc)

            sleep_secs = max(10, self._worker_interval_minutes * 60)
            if self._stop_worker_event.wait(timeout=sleep_secs):
                break


_GLOBAL_SCREENER_CACHE: Optional[StockScreenerCache] = None
_GLOBAL_CACHE_LOCK = threading.Lock()


def get_screener_cache() -> StockScreenerCache:
    """Retrieve or initialize the global thread-safe StockScreenerCache singleton."""
    global _GLOBAL_SCREENER_CACHE
    with _GLOBAL_CACHE_LOCK:
        if _GLOBAL_SCREENER_CACHE is None:
            _GLOBAL_SCREENER_CACHE = StockScreenerCache(seed_defaults=True)
        return _GLOBAL_SCREENER_CACHE
