"""FastAPI Backend Server for Options Suggester.

Provides REST endpoints for Next.js frontend:
- Real-time stock quotes, metadata & earnings blackout checks
- Historical OHLCV candlestick bars with SMA overlays formatted for TradingView Lightweight Charts
- Quantitative momentum, recency sentiment & trade signals
- Delta-targeted (0.30-0.55) options recommendations & institutional trade plans
- Commodities universe scanner (Precious Metals, Energy, Industrial Metals, Agriculture, Uranium)
- High-confidence AI ecosystem scanner (Chips, NeoClouds, Opticals, Memory, Software, Infra)
- High-Risk & Asymmetric Speculative setups screener (Moonshots, Lotto Spreads, Crypto-Beta) with Uncapped Sizing
- 0DTE High-Velocity Flash Lab with intraday Black-Scholes Greeks and theta burn rates
"""

import os
# Bound glibc memory arenas on Linux/Render containers to prevent virtual & RSS memory bloat
os.environ.setdefault("MALLOC_ARENA_MAX", "2")

import gc
import re
import threading
from datetime import datetime, date, timezone, timedelta
import logging
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from analysis.screener_cache import get_screener_cache
from data.stock_universe import get_stock_universe, STOCK_SECTORS
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import pandas as pd

from config import (
    AppConfig, DEFAULT_CONFIG, WATCHLIST_CATEGORIES, EXPANDED_WATCHLIST,
    COMMODITIES_CATEGORIES, COMMODITIES_UNIVERSE,
    AI_STOCKS_CATEGORIES, AI_STOCKS_UNIVERSE,
    HIGH_RISK_CATEGORIES, HIGH_RISK_UNIVERSE, ZERO_DTE_UNIVERSE
)
from data.price_data import get_price_history, get_current_quote, get_earnings_info, get_candles_data, DEFAULT_TIMEFRAME_PERIODS
from data.news_data import get_company_news
from data.options_data import get_options_chains, get_options_chain_matrix
from analysis.momentum import analyze_momentum
from analysis.sentiment import analyze_news_sentiment
from analysis.signals import generate_signal, BiasDirection, ConfidenceTier, TradeSignal
from options.suggester import suggest_options, build_zero_dte_setup, ZeroDteTradeSetup, calculate_black_scholes_greeks, compute_position_sizing

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager: starts background screener cache worker if enabled and shuts down gracefully."""
    # Free tier cloud instances (e.g. Render with 512MB RAM) crash if continuous background
    # batch downloads run. Controlled via SCREENER_WORKER_ENABLED env var (default: 0).
    worker_enabled = os.environ.get("SCREENER_WORKER_ENABLED", "1").lower() in ("1", "true", "yes")
    if worker_enabled:
        try:
            cache = get_screener_cache()
            cache.start_background_worker(interval_minutes=30)
            logger.info("Stock screener cache worker initialized on startup (interval=30m).")
        except Exception as exc:
            logger.error("Failed to start stock screener worker on startup: %s", exc)
    else:
        logger.info(
            "Stock screener background worker disabled (SCREENER_WORKER_ENABLED=0). "
            "Running in memory-safe cloud mode (<100MB RAM) using pre-warmed seed cache & on-demand scanning."
        )

    yield

    if worker_enabled:
        try:
            cache = get_screener_cache()
            cache.stop_background_worker(timeout=2.0)
        except Exception as exc:
            logger.error("Error stopping stock screener worker: %s", exc)


app = FastAPI(
    title="Options Suggester API",
    description="Quantitative Options Signal Engine with Delta Targeting, Commodities Universe, AI Sectors, and Uncapped High-Risk Speculative Setups",
    version="2.3.0",
    lifespan=lifespan,
)

# Enable CORS for Next.js frontend and any local origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def sanitize_json(data: Any) -> Any:
    """Recursively convert numpy types, NaN, and dates to clean JSON-serializable Python primitives."""
    if isinstance(data, dict):
        return {k: sanitize_json(v) for k, v in data.items()}
    elif isinstance(data, (list, tuple)):
        return [sanitize_json(v) for v in data]
    elif hasattr(data, "item"):
        val = data.item()
        if isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
            return None
        return val
    elif isinstance(data, float) and (np.isnan(data) or np.isinf(data)):
        return None
    elif isinstance(data, (datetime, date)):
        return data.isoformat()
    return data


def format_trade_plan_dict(tp: Any) -> Optional[Dict[str, Any]]:
    """Format OptionTradePlan into JSON-friendly dict."""
    if not tp:
        return None
    return {
        "entry_limit_price": getattr(tp, "entry_limit_price", 0.0),
        "entry_market_price": getattr(tp, "entry_market_price", 0.0),
        "entry_zone": getattr(tp, "entry_zone", ""),
        "underlying_spot": getattr(tp, "underlying_spot", 0.0),
        "underlying_invalidation_price": getattr(tp, "underlying_invalidation_price", 0.0),
        "tp1": {
            "option_price": getattr(tp, "tp1_option_price", 0.0),
            "dollar_gain": getattr(tp, "tp1_dollar_gain", 0.0),
            "underlying_target": getattr(tp, "tp1_underlying_target", 0.0),
            "gain_pct": getattr(tp, "tp1_gain_pct", 50.0),
            "action": getattr(tp, "tp1_action", ""),
        },
        "tp2": {
            "option_price": getattr(tp, "tp2_option_price", 0.0),
            "dollar_gain": getattr(tp, "tp2_dollar_gain", 0.0),
            "underlying_target": getattr(tp, "tp2_underlying_target", 0.0),
            "gain_pct": getattr(tp, "tp2_gain_pct", 100.0),
            "action": getattr(tp, "tp2_action", ""),
        },
        "tp3": {
            "option_price": getattr(tp, "tp3_runner_price", 0.0),
            "dollar_gain": getattr(tp, "tp3_dollar_gain", 0.0),
            "underlying_target": getattr(tp, "tp3_underlying_target", 0.0),
            "gain_pct": getattr(tp, "tp3_gain_pct", 150.0),
            "action": getattr(tp, "tp3_action", ""),
        },
        "stop_loss": {
            "option_price": getattr(tp, "stop_loss_option_price", 0.0),
            "dollar_loss": getattr(tp, "stop_loss_dollar_loss", 0.0),
            "planned_risk": getattr(tp, "total_planned_risk", 0.0),
            "total_planned_risk": getattr(tp, "total_planned_risk", 0.0),
            "max_capital_loss": getattr(tp, "max_capital_loss", 0.0),
            "rule": getattr(tp, "stop_loss_rule", ""),
        },
        "time_stop": {
            "daily_theta_decay": getattr(tp, "daily_theta_decay", 0.0),
            "max_holding_period_days": getattr(tp, "max_holding_period_days", 10),
            "rule": getattr(tp, "time_stop_rule", ""),
        },
        "metrics": {
            "pop_pct": getattr(tp, "probability_of_profit_pct", 50.0),
            "probability_of_profit_pct": getattr(tp, "probability_of_profit_pct", 50.0),
            "risk_reward_ratio": getattr(tp, "risk_reward_ratio", 2.0),
            "expected_value": getattr(tp, "expected_value_per_contract", 0.0),
            "expected_value_per_contract": getattr(tp, "expected_value_per_contract", 0.0),
        },
        "playbook_steps": getattr(tp, "playbook_steps", []),
        "ratchet_ladder": getattr(tp, "ratchet_ladder", []),
        "rolling_playbook": getattr(tp, "rolling_playbook", {}),
        "broker_bracket_order": getattr(tp, "broker_bracket_order", {}),
    }


@app.get("/api/health")
def health_check():
    """Health check endpoint with memory diagnostics for cloud container monitoring."""
    mem_info = {}
    try:
        import psutil
        process = psutil.Process()
        mem_info = {
            "rss_mb": round(process.memory_info().rss / (1024 * 1024), 2),
            "vms_mb": round(process.memory_info().vms / (1024 * 1024), 2),
        }
    except Exception:
        pass
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "memory": mem_info,
    }


@app.get("/api/universe")
def get_universe():
    """Return categorized stock watchlists, commodities universe, AI universe, and high-risk universe."""
    return sanitize_json({
        "categories": WATCHLIST_CATEGORIES,
        "all_tickers": EXPANDED_WATCHLIST,
        "commodities_categories": COMMODITIES_CATEGORIES,
        "commodities_universe": COMMODITIES_UNIVERSE,
        "ai_categories": AI_STOCKS_CATEGORIES,
        "ai_universe": AI_STOCKS_UNIVERSE,
        "high_risk_categories": HIGH_RISK_CATEGORIES,
        "high_risk_universe": HIGH_RISK_UNIVERSE,
        "zero_dte_universe": ZERO_DTE_UNIVERSE,
    })



@app.get("/api/candles")
def get_candles_endpoint(
    ticker: str = "NVDA",
    interval: str = "1d",
    period: Optional[str] = None,
):
    """Return historical or intraday OHLCV candlestick bars formatted for TradingView with SMA and VWAP."""
    ticker = ticker.strip().upper()
    candles = get_candles_data(ticker, interval=interval, period=period)
    if not candles:
        raise HTTPException(status_code=404, detail=f"No candle data available for {ticker} (interval={interval})")
    return sanitize_json({
        "symbol": ticker,
        "interval": interval,
        "period": period or DEFAULT_TIMEFRAME_PERIODS.get(interval.lower(), "6mo"),
        "count": len(candles),
        "candles": candles,
    })


@app.get("/api/stock-analysis")
def get_stock_analysis(
    ticker: str = "NVDA",
    period: str = "6mo",
    interval: str = "1d",
    equity: float = 10000.0,
    risk_pct: float = 1.0,
    min_dte: int = 14,
    max_dte: int = 45,
):
    """Complete deep dive for a single stock: chart data, momentum, sentiment, signal, options, and high-risk setup."""
    ticker = ticker.strip().upper()
    cfg = AppConfig()
    cfg.history_period = period
    cfg.risk.account_equity = float(equity)
    cfg.risk.max_risk_pct = float(risk_pct) / 100.0
    cfg.options_filter.min_dte = int(min_dte)
    cfg.options_filter.max_dte = int(max_dte)

    quote = get_current_quote(ticker)
    if not quote["valid"]:
        raise HTTPException(status_code=404, detail=f"Invalid or unavailable ticker symbol: {ticker}")

    hist = get_price_history(ticker, period=cfg.history_period)
    if hist is None or hist.empty:
        raise HTTPException(status_code=500, detail=f"Could not retrieve historical data for: {ticker}")

    # Fetch formatted candlestick bars with indicators and VWAP
    candles = get_candles_data(ticker, interval=interval, period=period)

    earnings_info = get_earnings_info(ticker, cfg.earnings.blackout_days, cfg.earnings.warning_days)
    momentum = analyze_momentum(hist, ticker, cfg.technicals)
    news_articles = get_company_news(ticker, limit=cfg.news_limit)
    sentiment = analyze_news_sentiment(news_articles, ticker)
    signal = generate_signal(momentum, sentiment, earnings_info, cfg.weights, cfg.earnings)

    # Options chain screening (disciplined + high-risk asymmetric)
    calls_df, puts_df, _ = get_options_chains(ticker, cfg.options_filter.min_dte, cfg.options_filter.max_dte)
    screening = suggest_options(
        signal, quote["current_price"], calls_df, puts_df,
        cfg.options_filter, cfg.risk, cfg.high_risk_filter
    )

    hr = screening.high_risk_setup
    hr_dict = None
    if hr:
        ls = hr.lotto_spread
        hr_dict = {
            "setup_name": hr.setup_name,
            "contract": hr.contract_symbol,
            "type": hr.option_type,
            "strike": hr.strike,
            "delta": hr.delta,
            "expiration": hr.expiration,
            "dte": hr.dte,
            "bid": hr.bid,
            "ask": hr.ask,
            "moneyness_pct": hr.moneyness_pct,
            "breakeven": hr.breakeven_price,
            "req_move_pct": hr.required_move_pct,
            "upside_leverage": hr.upside_leverage,
            "suggested_contracts": hr.suggested_contracts,
            "total_dollar_risk": hr.total_dollar_risk,
            "lotto_spread": {
                "type": ls.spread_type,
                "expiration": ls.expiration,
                "dte": ls.dte,
                "long_strike": ls.long_strike,
                "short_strike": ls.short_strike,
                "net_debit": ls.net_debit,
                "max_profit": ls.max_profit_per_contract,
                "risk_reward_ratio": ls.risk_reward_ratio,
                "notes": ls.spread_notes,
                "trade_plan": ls.trade_plan,
            } if ls else None,
            "warnings": hr.risk_warnings,
            "trade_plan": hr.trade_plan,
        }

    result = {
        "symbol": ticker,
        "quote": quote,
        "candles": candles,
        "earnings": earnings_info,
        "momentum": {
            "score": momentum.momentum_score,
            "trend_desc": momentum.trend_description,
            "rsi": momentum.rsi,
            "macd_hist": momentum.macd_hist,
            "macd_line": momentum.macd_line,
            "macd_signal": momentum.macd_signal,
            "sma_short": momentum.sma_short,
            "sma_long": momentum.sma_long,
            "volume_ratio": momentum.volume_ratio,
            "volume_confirmed": momentum.volume_confirmed,
            "weekly_trend": momentum.weekly_trend,
            "multi_timeframe_aligned": momentum.multi_timeframe_aligned,
        },
        "sentiment": {
            "score": sentiment.overall_score,
            "label": sentiment.sentiment_label,
            "article_count": sentiment.article_count,
            "positive_count": sentiment.positive_count,
            "negative_count": sentiment.negative_count,
            "neutral_count": sentiment.neutral_count,
            "articles": sentiment.scored_articles[:6],
        },
        "signal": {
            "bias": signal.bias.value,
            "combined_score": signal.combined_score,
            "confidence_pct": round(signal.confidence * 100, 1),
            "confidence_tier": signal.confidence_tier.value,
            "is_earnings_blackout": signal.is_earnings_blackout,
            "action_suggestion": signal.action_suggestion,
            "rationale": signal.rationale,
        },
        "options": {
            "single_leg": [
                {
                    "rank": idx + 1,
                    "contract": s.contract_symbol,
                    "type": s.option_type,
                    "strike": s.strike,
                    "delta": s.delta,
                    "gamma": getattr(s, "gamma", 0.0),
                    "theta": getattr(s, "theta", 0.0),
                    "vega": getattr(s, "vega", 0.0),
                    "expiration": s.expiration,
                    "dte": s.dte,
                    "bid": s.bid,
                    "ask": s.ask,
                    "mid": s.mid_price,
                    "spread_pct": s.spread_pct_of_mid,
                    "volume": s.volume,
                    "open_interest": s.open_interest,
                    "iv_pct": s.implied_volatility_pct,
                    "breakeven": s.breakeven_price,
                    "req_move_pct": s.required_move_pct,
                    "suggested_contracts": s.suggested_contracts,
                    "total_dollar_risk": s.total_dollar_risk,
                    "stop_loss_price": s.suggested_stop_loss_price,
                    "stop_loss_dollar": s.stop_loss_dollar_risk,
                    "rank_score": s.rank_score,
                    "warnings": s.risk_warnings,
                    "trade_plan": format_trade_plan_dict(s.trade_plan),
                }
                for idx, s in enumerate(screening.single_leg_suggestions)
            ],
            "debit_spreads": [
                {
                    "spread_type": spd.spread_type,
                    "expiration": spd.expiration,
                    "dte": spd.dte,
                    "long_contract": spd.long_contract,
                    "long_strike": spd.long_strike,
                    "long_ask": spd.long_ask,
                    "long_delta": spd.long_delta,
                    "short_contract": spd.short_contract,
                    "short_strike": spd.short_strike,
                    "short_bid": spd.short_bid,
                    "short_delta": spd.short_delta,
                    "net_debit": spd.net_debit,
                    "max_loss": spd.max_loss_per_contract,
                    "max_profit": spd.max_profit_per_contract,
                    "breakeven": spd.breakeven_price,
                    "risk_reward_ratio": spd.risk_reward_ratio,
                    "suggested_contracts": spd.suggested_contracts,
                    "total_dollar_risk": spd.total_dollar_risk,
                    "notes": spd.spread_notes,
                    "trade_plan": spd.trade_plan,
                }
                for spd in screening.spread_suggestions
            ],
            "high_risk_setup": hr_dict,
            "elevated_iv": bool(screening.elevated_iv),
            "avg_iv_pct": float(screening.avg_iv_pct),
            "audit_log": screening.audit_log,
        }
    }
    return sanitize_json(result)


@app.get("/api/high-confidence")
def get_high_confidence_picks(
    sector: str = "all_ai",
    min_confidence: float = 35.0,
    equity: float = 10000.0,
    risk_pct: float = 1.0,
):
    """Screen for higher-confidence option recommendations with focus on AI & Commodities stocks."""
    cfg = AppConfig()
    cfg.risk.account_equity = float(equity)
    cfg.risk.max_risk_pct = float(risk_pct) / 100.0

    if sector == "chips":
        tickers = AI_STOCKS_CATEGORIES["AI Chips & Semiconductors"]
    elif sector == "neoclouds":
        tickers = AI_STOCKS_CATEGORIES["AI NeoClouds & GPU Compute"]
    elif sector == "opticals":
        tickers = AI_STOCKS_CATEGORIES["AI Optical Interconnect & Photonics"]
    elif sector == "memory":
        tickers = AI_STOCKS_CATEGORIES["AI Memory & Storage (HBM)"]
    elif sector == "software":
        tickers = AI_STOCKS_CATEGORIES["AI Enterprise Software & Cyber"]
    elif sector == "infra":
        tickers = AI_STOCKS_CATEGORIES["AI Hardware & Data Center Infra"]
    elif sector == "mag7":
        tickers = WATCHLIST_CATEGORIES["Mega-Cap Tech"]
    elif sector == "commodities":
        tickers = COMMODITIES_UNIVERSE
    elif sector == "precious_metals":
        tickers = COMMODITIES_CATEGORIES["Precious Metals & Miners"]
    elif sector == "energy_commodities":
        tickers = COMMODITIES_CATEGORIES["Energy, Crude & Natural Gas"]
    elif sector == "industrial_metals":
        tickers = COMMODITIES_CATEGORIES["Industrial Metals, Copper & Materials"]
    else:
        tickers = AI_STOCKS_UNIVERSE

    results = []
    for sym in tickers:
        try:
            quote = get_current_quote(sym)
            if not quote["valid"]:
                continue

            hist = get_price_history(sym, period=cfg.history_period)
            if hist is None:
                continue

            e_info = get_earnings_info(sym, cfg.earnings.blackout_days, cfg.earnings.warning_days)
            if e_info.get("is_blackout"):
                continue

            mom = analyze_momentum(hist, sym, cfg.technicals)
            articles = get_company_news(sym, limit=5)
            sent = analyze_news_sentiment(articles, sym)
            sig = generate_signal(mom, sent, e_info, cfg.weights, cfg.earnings)

            conf_pct = sig.confidence * 100.0
            if conf_pct < float(min_confidence) or sig.bias == BiasDirection.NEUTRAL:
                continue

            calls_df, puts_df, _ = get_options_chains(sym, cfg.options_filter.min_dte, cfg.options_filter.max_dte)
            screening = suggest_options(
                sig, quote["current_price"], calls_df, puts_df,
                cfg.options_filter, cfg.risk, cfg.high_risk_filter
            )

            if screening.single_leg_suggestions:
                best = screening.single_leg_suggestions[0]
                spd = screening.spread_suggestions[0] if screening.spread_suggestions else None
                hr = screening.high_risk_setup
                results.append({
                    "symbol": sym,
                    "name": quote["name"],
                    "price": quote["current_price"],
                    "change_pct": quote["change_percent"],
                    "bias": sig.bias.value,
                    "confidence_pct": round(conf_pct, 1),
                    "confidence_tier": sig.confidence_tier.value,
                    "momentum_score": mom.momentum_score,
                    "volume_ratio": mom.volume_ratio,
                    "volume_confirmed": mom.volume_confirmed,
                    "weekly_trend": mom.weekly_trend,
                    "sentiment_score": sent.overall_score,
                    "top_option": {
                        "contract": best.contract_symbol,
                        "type": best.option_type,
                        "strike": best.strike,
                        "delta": best.delta,
                        "expiration": best.expiration,
                        "dte": best.dte,
                        "bid": best.bid,
                        "ask": best.ask,
                        "spread_pct": best.spread_pct_of_mid,
                        "breakeven": best.breakeven_price,
                        "req_move_pct": best.required_move_pct,
                        "contracts": best.suggested_contracts,
                        "total_risk": best.total_dollar_risk,
                        "stop_loss": best.suggested_stop_loss_price,
                        "trade_plan": format_trade_plan_dict(best.trade_plan),
                    },
                    "debit_spread": {
                        "type": spd.spread_type,
                        "long_strike": spd.long_strike,
                        "short_strike": spd.short_strike,
                        "net_debit": spd.net_debit,
                        "max_profit": spd.max_profit_per_contract,
                        "risk_reward_ratio": spd.risk_reward_ratio,
                        "trade_plan": spd.trade_plan,
                    } if spd else None,
                    "high_risk_setup": {
                        "setup_name": hr.setup_name,
                        "contract": hr.contract_symbol,
                        "strike": hr.strike,
                        "delta": hr.delta,
                        "expiration": hr.expiration,
                        "dte": hr.dte,
                        "ask": hr.ask,
                        "upside_leverage": hr.upside_leverage,
                        "total_dollar_risk": hr.total_dollar_risk,
                        "trade_plan": hr.trade_plan,
                    } if hr else None,
                    "rationale": sig.rationale[:4],
                })
        except Exception as exc:
            logger.warning("Error screening %s: %s", sym, exc)

    results.sort(key=lambda x: x["confidence_pct"], reverse=True)
    return sanitize_json({"count": len(results), "picks": results})


@app.get("/api/high-risk-setups")
def get_high_risk_setups(
    category: str = "all_speculative",
    ticker: Optional[str] = None,
    equity: float = 10000.0,
    risk_pct: float = 1.0,
):
    """Screen for aggressive, asymmetric high-risk trade setups with uncapped sizing based on risk budget."""
    cfg = AppConfig()
    cfg.risk.account_equity = float(equity)
    effective_risk = float(risk_pct) / 100.0
    cfg.risk.max_risk_pct = effective_risk
    cfg.high_risk_filter.speculative_risk_pct = effective_risk

    if ticker:
        tickers = [ticker.strip().upper()]
    elif category == "crypto_beta":
        tickers = HIGH_RISK_CATEGORIES["Crypto-Beta & AI Miners"]
    elif category == "spec_tech":
        tickers = HIGH_RISK_CATEGORIES["Speculative Tech & Quantum"]
    elif category == "high_vol":
        tickers = HIGH_RISK_CATEGORIES["High-Vol Fintech & Squeeze Growth"]
    elif category == "commodities":
        tickers = COMMODITIES_UNIVERSE
    elif category == "precious_metals":
        tickers = COMMODITIES_CATEGORIES["Precious Metals & Miners"]
    elif category == "energy_commodities":
        tickers = COMMODITIES_CATEGORIES["Energy, Crude & Natural Gas"]
    elif category == "industrial_metals":
        tickers = COMMODITIES_CATEGORIES["Industrial Metals, Copper & Materials"]
    elif category == "zero_dte":
        tickers = ZERO_DTE_UNIVERSE
    else:
        tickers = HIGH_RISK_UNIVERSE

    setups = []
    for sym in tickers:
        try:
            quote = get_current_quote(sym)
            if not quote["valid"]:
                continue

            hist = get_price_history(sym, period=cfg.history_period)
            if hist is None:
                continue

            e_info = get_earnings_info(sym, cfg.earnings.blackout_days, cfg.earnings.warning_days)
            mom = analyze_momentum(hist, sym, cfg.technicals)
            articles = get_company_news(sym, limit=4)
            sent = analyze_news_sentiment(articles, sym)
            sig = generate_signal(mom, sent, e_info, cfg.weights, cfg.earnings)

            if sig.bias == BiasDirection.NEUTRAL:
                # Derive directional lean for speculative trade setups
                sig.bias = BiasDirection.BULLISH if mom.momentum_score >= 50 else BiasDirection.BEARISH
                if sig.confidence < 0.25:
                    sig.confidence = 0.25

            sig_for_options = TradeSignal(
                symbol=sig.symbol,
                bias=sig.bias,
                combined_score=sig.combined_score,
                confidence=sig.confidence,
                confidence_tier=sig.confidence_tier,
                momentum_score=sig.momentum_score,
                sentiment_score=sig.sentiment_score,
                is_earnings_blackout=False,
                earnings_info=sig.earnings_info,
                rationale=sig.rationale,
                action_suggestion=sig.action_suggestion,
            )

            calls_df, puts_df, _ = get_options_chains(sym, cfg.high_risk_filter.min_dte, cfg.high_risk_filter.max_dte)
            screening = suggest_options(
                sig_for_options, quote["current_price"], calls_df, puts_df,
                cfg.options_filter, cfg.risk, cfg.high_risk_filter
            )

            hr = screening.high_risk_setup
            if hr:
                ls = hr.lotto_spread
                setups.append({
                    "symbol": sym,
                    "name": quote["name"],
                    "price": quote["current_price"],
                    "change_pct": quote["change_percent"],
                    "bias": sig.bias.value,
                    "confidence_pct": round(sig.confidence * 100.0, 1),
                    "momentum_score": mom.momentum_score,
                    "volume_ratio": mom.volume_ratio,
                    "setup_name": hr.setup_name,
                    "contract": hr.contract_symbol,
                    "type": hr.option_type,
                    "strike": hr.strike,
                    "delta": hr.delta,
                    "expiration": hr.expiration,
                    "dte": hr.dte,
                    "bid": hr.bid,
                    "ask": hr.ask,
                    "moneyness_pct": hr.moneyness_pct,
                    "breakeven": hr.breakeven_price,
                    "req_move_pct": hr.required_move_pct,
                    "upside_leverage": hr.upside_leverage,
                    "suggested_contracts": hr.suggested_contracts,
                    "total_dollar_risk": hr.total_dollar_risk,
                    "lotto_spread": {
                        "type": ls.spread_type,
                        "expiration": ls.expiration,
                        "dte": ls.dte,
                        "long_strike": ls.long_strike,
                        "short_strike": ls.short_strike,
                        "net_debit": ls.net_debit,
                        "max_profit": ls.max_profit_per_contract,
                        "risk_reward_ratio": ls.risk_reward_ratio,
                        "suggested_contracts": ls.suggested_contracts,
                        "total_dollar_risk": ls.total_dollar_risk,
                        "notes": ls.spread_notes,
                        "trade_plan": ls.trade_plan,
                    } if ls else None,
                    "warnings": hr.risk_warnings,
                    "trade_plan": hr.trade_plan,
                })
        except Exception as exc:
            logger.warning("Error screening high risk for %s: %s", sym, exc)

    # Sort by upside leverage ratio descending
    setups.sort(key=lambda x: x["upside_leverage"], reverse=True)
    return sanitize_json({"count": len(setups), "setups": setups})


@app.get("/api/zero-dte")
def get_zero_dte_endpoint(
    ticker: Optional[str] = None,
    equity: float = 10000.0,
    risk_pct: float = 1.0,
):
    """Scan and generate high-velocity 0DTE (same-day / front-session) options trade setups."""
    cfg = AppConfig()
    cfg.risk.account_equity = float(equity)
    effective_risk = float(risk_pct) / 100.0
    cfg.risk.max_risk_pct = effective_risk
    cfg.zero_dte_filter.speculative_risk_pct = effective_risk

    tickers = [ticker.strip().upper()] if ticker else ZERO_DTE_UNIVERSE
    results = []

    for sym in tickers:
        try:
            quote = get_current_quote(sym)
            if not quote["valid"]:
                continue

            hist = get_price_history(sym, period=cfg.history_period)
            if hist is None:
                continue

            mom = analyze_momentum(hist, sym, cfg.technicals)
            articles = get_company_news(sym, limit=3)
            sent = analyze_news_sentiment(articles, sym)
            sig = generate_signal(mom, sent, None, cfg.weights, cfg.earnings)

            # Intraday momentum bias (if neutral, lean towards technical momentum)
            bias = sig.bias
            if bias == BiasDirection.NEUTRAL:
                bias = BiasDirection.BULLISH if mom.momentum_score >= 50 else BiasDirection.BEARISH

            opt_type = "CALL" if bias == BiasDirection.BULLISH else "PUT"

            # Retrieve front-month chain (0 to 1 DTE)
            calls_df, puts_df, exps = get_options_chains(sym, min_dte=0, max_dte=1)
            target_chain = calls_df if opt_type == "CALL" else puts_df

            setup = build_zero_dte_setup(
                target_chain, opt_type, quote["current_price"],
                cfg.zero_dte_filter, cfg.risk,
                symbol=sym, bias_str=bias.value
            )

            # Build comprehensive list of all available 0DTE options for this symbol
            all_opts = []
            exp_target = setup.expiration if setup else (calls_df["expiration"].iloc[0] if not calls_df.empty else (puts_df["expiration"].iloc[0] if not puts_df.empty else None))
            dte_val = setup.dte if setup else (int(calls_df["dte"].iloc[0]) if not calls_df.empty else 0)

            if exp_target:
                for is_call, df in [(True, calls_df), (False, puts_df)]:
                    if df is None or df.empty:
                        continue
                    exp_df = df[df["expiration"] == exp_target]
                    for _, row in exp_df.iterrows():
                        k = float(row["strike"])
                        ask_v = float(row["ask"])
                        bid_v = float(row["bid"])
                        mid_v = round((bid_v + ask_v) / 2.0, 2)
                        spread_v = round(max(0.0, ask_v - bid_v), 2)
                        spread_p = round((spread_v / mid_v) * 100.0, 1) if mid_v > 0 else 0.0
                        iv_v = float(row.get("impliedVolatility", 0.20))
                        g = calculate_black_scholes_greeks(quote["current_price"], k, dte_val, iv_v, is_call)
                        
                        moneyness = round(((k / quote["current_price"]) - 1.0) * 100.0, 2) if is_call else round(((quote["current_price"] / k) - 1.0) * 100.0, 2)
                        be_v = round(k + ask_v, 2) if is_call else round(k - ask_v, 2)
                        req_m = round(((be_v - quote["current_price"]) / quote["current_price"]) * 100.0, 2) if is_call else round(((quote["current_price"] - be_v) / quote["current_price"]) * 100.0, 2)
                        contracts_c, total_r, stop_px, _ = compute_position_sizing(ask_v, cfg.risk, custom_risk_pct=cfg.zero_dte_filter.speculative_risk_pct)
                        
                        all_opts.append({
                            "contract": str(row["contractSymbol"]),
                            "strike": k,
                            "type": "CALL" if is_call else "PUT",
                            "expiration": exp_target,
                            "dte": dte_val,
                            "bid": bid_v,
                            "ask": ask_v,
                            "mid": mid_v,
                            "spread": spread_v,
                            "spread_pct": spread_p,
                            "volume": int(row.get("volume", 0)),
                            "open_interest": int(row.get("openInterest", 0)),
                            "iv_pct": round(iv_v * 100.0, 1),
                            "in_the_money": bool(row.get("inTheMoney", False)),
                            "delta": round(g.delta, 3),
                            "gamma": round(g.gamma, 4),
                            "theta": round(g.theta, 3),
                            "theta_per_hour": round(g.theta / 6.5, 3),
                            "moneyness_pct": moneyness,
                            "breakeven": be_v,
                            "req_move_pct": req_m,
                            "suggested_contracts": contracts_c,
                            "total_dollar_risk": total_r,
                            "stop_loss_price": stop_px,
                        })

                all_opts.sort(key=lambda x: (x["strike"], 0 if x["type"] == "CALL" else 1))

            if setup:
                ls = setup.lotto_spread
                results.append({
                    "symbol": sym,
                    "name": quote.get("name", sym),
                    "price": quote["current_price"],
                    "change_pct": quote.get("change_percent", 0.0),
                    "bias": bias.value,
                    "confidence_pct": round(max(sig.confidence, 0.40) * 100.0, 1),
                    "momentum_score": mom.momentum_score,
                    "volume_ratio": mom.volume_ratio,
                    "expiration": setup.expiration,
                    "dte": setup.dte,
                    "scalp_setup": {
                        "contract": setup.scalp_contract,
                        "strike": setup.scalp_strike,
                        "type": setup.scalp_type,
                        "bid": setup.scalp_bid,
                        "ask": setup.scalp_ask,
                        "delta": setup.scalp_delta,
                        "gamma": setup.scalp_gamma,
                        "theta": setup.scalp_theta,
                        "theta_per_hour": setup.scalp_theta_per_hour,
                        "contracts": setup.scalp_suggested_contracts,
                        "total_risk": setup.scalp_total_risk,
                        "breakeven": setup.scalp_breakeven,
                        "req_move_pct": setup.scalp_req_move_pct,
                    },
                    "lotto_setup": {
                        "contract": setup.lotto_contract,
                        "strike": setup.lotto_strike,
                        "bid": setup.lotto_bid,
                        "ask": setup.lotto_ask,
                        "delta": setup.lotto_delta,
                        "gamma": setup.lotto_gamma,
                        "upside_leverage": setup.lotto_upside_leverage,
                        "contracts": setup.lotto_suggested_contracts,
                        "total_risk": setup.lotto_total_risk,
                        "breakeven": setup.lotto_breakeven,
                        "req_move_pct": setup.lotto_req_move_pct,
                    },
                    "lotto_spread": {
                        "type": ls.spread_type,
                        "expiration": ls.expiration,
                        "dte": ls.dte,
                        "long_strike": ls.long_strike,
                        "short_strike": ls.short_strike,
                        "net_debit": ls.net_debit,
                        "max_profit": ls.max_profit_per_contract,
                        "risk_reward_ratio": ls.risk_reward_ratio,
                        "contracts": ls.suggested_contracts,
                        "total_risk": ls.total_dollar_risk,
                        "notes": ls.spread_notes,
                        "trade_plan": ls.trade_plan,
                    } if ls else None,
                    "breakeven_velocity_per_hour": setup.breakeven_velocity_per_hour,
                    "warnings": setup.risk_warnings,
                    "trade_plan": setup.trade_plan,
                    "all_options": all_opts,
                })
            elif ticker and all_opts:
                # Custom search ticker: return with full available options chain even if no strict scalp filtered
                results.append({
                    "symbol": sym,
                    "name": quote.get("name", sym),
                    "price": quote["current_price"],
                    "change_pct": quote.get("change_percent", 0.0),
                    "bias": bias.value,
                    "confidence_pct": round(max(sig.confidence, 0.40) * 100.0, 1),
                    "momentum_score": mom.momentum_score,
                    "volume_ratio": mom.volume_ratio,
                    "expiration": exp_target or "Front Cycle",
                    "dte": dte_val,
                    "scalp_setup": None,
                    "lotto_setup": None,
                    "lotto_spread": None,
                    "breakeven_velocity_per_hour": 0.0,
                    "warnings": ["Custom search: Full available 0DTE options chain loaded."],
                    "trade_plan": None,
                    "all_options": all_opts,
                })
        except Exception as exc:
            logger.warning("Error screening 0DTE for %s: %s", sym, exc)

    return sanitize_json({"count": len(results), "setups": results})


@app.get("/api/options-chain")
def get_options_chain_endpoint(
    ticker: str = "NVDA",
    expiration: Optional[str] = None
):
    """Retrieve full interactive options chain matrix with Black-Scholes Greeks, Max Pain, and Expected Move."""
    ticker = ticker.strip().upper()
    try:
        matrix = get_options_chain_matrix(ticker, expiration)
        return sanitize_json(matrix)
    except Exception as exc:
        logger.error("Error retrieving options chain for %s: %s", ticker, exc)
        raise HTTPException(status_code=500, detail=str(exc))



@app.get("/api/market-ribbon")
def get_market_ribbon_endpoint():
    """Retrieve fast cached quotes and market session status for top benchmark indices."""
    try:
        from data.price_data import get_market_ribbon_data
        data = get_market_ribbon_data()
        return sanitize_json(data)
    except Exception as exc:
        logger.error("Error retrieving market ribbon: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/watchlist-summary")
def get_watchlist_summary_endpoint(tickers: str = "NVDA,AAPL,SPY,TSLA,QQQ"):
    """Retrieve real-time quote, daily change, and momentum metrics for a list of tickers."""
    syms = [s.strip().upper() for s in tickers.split(",") if s.strip()]
    if not syms:
        return sanitize_json({"count": 0, "tickers": []})
    try:
        from data.price_data import get_watchlist_summary
        items = get_watchlist_summary(syms[:25])
        return sanitize_json({"count": len(items), "tickers": items})
    except Exception as exc:
        logger.error("Error retrieving watchlist summary: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))



@app.get("/api/volatility-cockpit")
def get_volatility_cockpit_endpoint(ticker: str = "NVDA"):
    """Retrieve full Volatility Cockpit: IV Rank, IV Percentile, 1-yr HV envelope,

    Volatility Risk Premium (VRP), Term Structure, and 1-Sigma Expected Move Cones.
    """
    ticker = ticker.strip().upper()
    try:
        from data.options_data import get_volatility_cockpit
        data = get_volatility_cockpit(ticker)
        if not data or "error" in data:
            raise HTTPException(status_code=404, detail=data.get("error", f"Could not compute volatility cockpit for {ticker}"))
        return sanitize_json(data)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error retrieving volatility cockpit for %s: %s", ticker, exc)
        raise HTTPException(status_code=500, detail=str(exc))



def parse_occ_symbol(contract: str) -> Optional[Dict[str, Any]]:
    """Parse OCC option symbol (e.g. NVDA261016C00230000) into root, expiration, type, and strike."""
    if not contract or not isinstance(contract, str):
        return None
    m = re.match(r"^([A-Z]{1,6})(\d{2})(\d{2})(\d{2})([CP])(\d{8})$", contract.strip().upper())
    if not m:
        return None
    root, yy, mm, dd, cp, strike_raw = m.groups()
    return {
        "ticker": root,
        "expiration": f"20{yy}-{mm}-{dd}",
        "option_type": "CALL" if cp == "C" else "PUT",
        "strike": int(strike_raw) / 1000.0,
    }


def check_is_expired(expiration_str: Optional[str]) -> bool:
    """Check if an option expiration date has expired in US Eastern Time (4:00 PM ET close)."""
    if not expiration_str:
        return False
    try:
        exp_d = datetime.strptime(str(expiration_str).strip()[:10], "%Y-%m-%d").date()
        try:
            import zoneinfo
            et_now = datetime.now(zoneinfo.ZoneInfo("America/New_York"))
        except Exception:
            et_now = datetime.now(timezone.utc) - timedelta(hours=4)

        if exp_d < et_now.date():
            return True
        if exp_d == et_now.date() and et_now.hour >= 16:
            return True
        return False
    except Exception:
        return False


def fetch_paper_quotes(items_to_quote: List[Any]) -> Dict[str, Any]:
    """Fetch live or recent market quotes for stock tickers and options contracts with automatic expiration settlement."""
    if not items_to_quote:
        return {"quotes": {}}

    extracted: List[Dict[str, Any]] = []
    for it in items_to_quote:
        if isinstance(it, str):
            sym = it.strip().upper()
            if sym:
                occ_info = parse_occ_symbol(sym)
                is_opt = occ_info is not None or (len(sym) > 6 and any(ch.isdigit() for ch in sym))
                extracted.append({
                    "key": sym,
                    "symbol": sym,
                    "asset_type": "OPTION" if is_opt else "STOCK",
                    "ticker": occ_info["ticker"] if occ_info else sym,
                    "expiration": occ_info["expiration"] if occ_info else None,
                    "option_type": occ_info["option_type"] if occ_info else "CALL",
                    "strike": occ_info["strike"] if occ_info else None,
                })
        elif isinstance(it, dict):
            sym = (it.get("symbol") or it.get("contract") or it.get("ticker") or "").strip().upper()
            if not sym:
                continue
            key = (it.get("contract") or it.get("symbol") or sym).strip().upper()
            occ_info = parse_occ_symbol(key) or parse_occ_symbol(sym)
            asset_type = (it.get("asset_type") or it.get("type") or "").strip().upper()
            if not asset_type:
                is_opt = occ_info is not None or (len(sym) > 6 and any(ch.isdigit() for ch in sym))
                asset_type = "OPTION" if is_opt else "STOCK"

            ticker = (it.get("ticker") or (occ_info["ticker"] if occ_info else sym)).strip().upper()
            exp_val = it.get("expiration") or (occ_info["expiration"] if occ_info else None)
            opt_type = (it.get("optionType") or it.get("option_type") or (occ_info["option_type"] if occ_info else "CALL")).strip().upper()
            strike_raw = it.get("strike") if it.get("strike") is not None else (occ_info["strike"] if occ_info else None)
            strike_val = None
            if strike_raw is not None:
                try:
                    strike_val = float(strike_raw)
                except (ValueError, TypeError):
                    strike_val = None

            extracted.append({
                "key": key,
                "symbol": sym,
                "asset_type": asset_type,
                "ticker": ticker,
                "expiration": exp_val,
                "option_type": opt_type,
                "strike": strike_val,
            })

    if not extracted:
        return {"quotes": {}}

    results: Dict[str, Any] = {}
    all_syms_set = []
    for it in extracted:
        if it["symbol"]:
            all_syms_set.append(it["symbol"])
        if it["ticker"]:
            all_syms_set.append(it["ticker"])
    all_syms = list(dict.fromkeys(all_syms_set))[:60]

    try:
        import yfinance as yf
        ticks = yf.Tickers(" ".join(all_syms))

        def _get_price(s: str) -> tuple[float, float]:
            try:
                t = ticks.tickers.get(s)
                fast = getattr(t, "fast_info", None) if t else None
                p = float(getattr(fast, "last_price", 0.0) or 0.0) if fast else 0.0
                pc = float(getattr(fast, "previous_close", 0.0) or 0.0) if fast else 0.0
                if p <= 0.0 and t:
                    hist = t.history(period="2d")
                    if hist is not None and not hist.empty:
                        p = float(hist["Close"].iloc[-1])
                        if len(hist) > 1:
                            pc = float(hist["Close"].iloc[-2])
                return (p, pc)
            except Exception:
                return (0.0, 0.0)

        for item in extracted:
            key = item["key"]
            sym = item["symbol"]
            asset_type = item["asset_type"]
            ticker = item["ticker"]
            opt_type = item["option_type"]
            strike = item["strike"]
            exp_date_str = item["expiration"]

            is_expired = False
            if asset_type == "OPTION" and exp_date_str:
                is_expired = check_is_expired(exp_date_str)

            underlying_spot = 0.0
            if asset_type == "OPTION" and ticker:
                underlying_spot, _ = _get_price(ticker)

            if is_expired:
                intrinsic = 0.0
                if strike is not None and underlying_spot > 0:
                    if opt_type == "CALL":
                        intrinsic = max(0.0, round(underlying_spot - strike, 2))
                    else:
                        intrinsic = max(0.0, round(strike - underlying_spot, 2))
                settlement_type = "EXPIRED_ITM" if intrinsic > 0.0 else "EXPIRED_WORTHLESS"
                results[key] = {
                    "symbol": sym,
                    "contract": key,
                    "asset_type": "OPTION",
                    "current_price": intrinsic,
                    "previous_close": 0.0,
                    "change": 0.0,
                    "change_pct": 0.0,
                    "valid": True,
                    "is_expired": True,
                    "settlement_price": intrinsic,
                    "settlement_type": settlement_type,
                    "underlying_symbol": ticker,
                    "underlying_spot": round(underlying_spot, 2) if underlying_spot > 0 else None,
                    "strike": strike,
                    "option_type": opt_type,
                    "expiration": exp_date_str,
                }
            else:
                px, prev_close = _get_price(sym)
                change = round(px - prev_close, 2) if (px > 0 and prev_close > 0) else 0.0
                change_pct = round((change / prev_close) * 100.0, 2) if prev_close > 0 else 0.0
                results[key] = {
                    "symbol": sym,
                    "contract": key,
                    "asset_type": asset_type,
                    "current_price": round(px, 2),
                    "previous_close": round(prev_close, 2),
                    "change": change,
                    "change_pct": change_pct,
                    "valid": px > 0,
                    "is_expired": False,
                    "settlement_price": None,
                    "settlement_type": None,
                    "underlying_symbol": ticker if asset_type == "OPTION" else None,
                    "underlying_spot": round(underlying_spot, 2) if underlying_spot > 0 else None,
                    "strike": strike,
                    "option_type": opt_type if asset_type == "OPTION" else None,
                    "expiration": exp_date_str,
                }
        return {"quotes": results}
    except Exception as exc:
        logger.error("Error retrieving paper quotes: %s", exc)
        for item in extracted:
            results[item["key"]] = {
                "symbol": item["symbol"],
                "contract": item["key"],
                "asset_type": item["asset_type"],
                "current_price": 0.0,
                "previous_close": 0.0,
                "valid": False,
                "is_expired": False,
            }
        return {"quotes": results}


@app.get("/api/paper-quotes")
def get_paper_quotes_endpoint(contracts: str = ""):
    """Retrieve current market price and quote data for active paper trading contracts."""
    contract_list = [c.strip().upper() for c in contracts.split(",") if c.strip()]
    return sanitize_json(fetch_paper_quotes(contract_list))


@app.post("/api/paper-quotes")
async def post_paper_quotes_endpoint(request: Request):
    """Retrieve current market quotes for active paper trading positions (both stocks and options)."""
    items: List[Any] = []
    try:
        body = await request.json()
        if isinstance(body, list):
            items = body
        elif isinstance(body, dict):
            if "items" in body and isinstance(body["items"], list):
                items = body["items"]
            elif "positions" in body and isinstance(body["positions"], list):
                items = body["positions"]
            elif "contracts" in body:
                c = body["contracts"]
                items = c if isinstance(c, list) else [x.strip() for x in str(c).split(",") if x.strip()]
            elif "symbols" in body:
                s = body["symbols"]
                items = s if isinstance(s, list) else [x.strip() for x in str(s).split(",") if x.strip()]
    except Exception:
        pass

    quotes = fetch_paper_quotes(items)
    return sanitize_json(quotes)


@app.get("/api/stocks/recommendations")
def get_stock_recommendations_endpoint(
    horizon: Optional[str] = None,
    sector: Optional[str] = None,
    strategy: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "score",
    limit: int = 50,
    offset: int = 0,
):
    """Query, filter, sort, and paginate cached stock recommendations in sub-second time."""
    cache = get_screener_cache()
    res = cache.get_recommendations(
        horizon=horizon,
        sector=sector,
        strategy=strategy,
        search=search,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
    )
    return sanitize_json(res)


@app.get("/api/stocks/universe")
def get_stocks_universe_endpoint():
    """Return categorized stock sectors, universe catalog, and sector ticker counts."""
    universe = get_stock_universe()
    sector_counts: Dict[str, int] = {}
    for item in universe:
        sec = item.get("sector", "other")
        sector_counts[sec] = sector_counts.get(sec, 0) + 1

    sectors_list = [
        {"key": k, "name": v, "count": sector_counts.get(k, 0)}
        for k, v in STOCK_SECTORS.items()
    ]
    return sanitize_json({
        "sectors": sectors_list,
        "sector_map": STOCK_SECTORS,
        "total_stocks": len(universe),
        "sector_counts": sector_counts,
    })


@app.get("/api/stocks/analysis")
def get_stocks_analysis_endpoint(
    symbol: Optional[str] = None,
    ticker: Optional[str] = None,
):
    """Retrieve full deep-dive stock analysis, trade plan, and momentum metrics."""
    target_symbol = symbol or ticker
    if not target_symbol or not target_symbol.strip():
        raise HTTPException(status_code=400, detail="Stock symbol parameter is required")

    target_symbol = target_symbol.strip().upper()
    cache = get_screener_cache()
    analysis = cache.get_analysis(target_symbol)
    if not analysis:
        raise HTTPException(
            status_code=404,
            detail=f"Stock analysis not available for symbol: {target_symbol}",
        )
    return sanitize_json(analysis)


@app.get("/api/stocks/status")
def get_stocks_status_endpoint():
    """Retrieve current screener cache status, counts, and background worker state."""
    cache = get_screener_cache()
    return sanitize_json(cache.get_status())


@app.post("/api/stocks/refresh")
async def post_stocks_refresh_endpoint(
    request: Request,
    force: bool = False,
):
    """Trigger manual cache refresh across stock universe or selected tickers."""
    req_force = force
    req_tickers: Optional[List[str]] = None
    try:
        body = await request.json()
        if isinstance(body, dict):
            if "force" in body:
                req_force = bool(body["force"])
            if "tickers" in body and isinstance(body["tickers"], list):
                req_tickers = [str(t).strip().upper() for t in body["tickers"] if t]
    except Exception:
        pass

    cache = get_screener_cache()
    res = cache.refresh_cache(force=req_force, tickers=req_tickers)
    return sanitize_json(res)


@app.get("/api/stocks/monte-carlo")
def get_stocks_monte_carlo_endpoint(
    symbol: Optional[str] = None,
    ticker: Optional[str] = None,
    simulations: int = 2000,
    days: int = 30,
    tp1: Optional[float] = None,
    stop_loss: Optional[float] = None,
):    
    """Execute vectorized Monte Carlo price projection simulation (GBM).

    Returns percentile fan-trajectories, target touch probabilities,
    first-touch win rate, and Value at Risk (VaR 95% & 99%).
    """
    from dataclasses import asdict
    from analysis.monte_carlo import run_monte_carlo_simulation

    target_symbol = (symbol or ticker or "").strip().upper()
    if not target_symbol:
        raise HTTPException(status_code=400, detail="Stock symbol parameter is required")

    quote = get_current_quote(target_symbol)
    cur_price = float(quote.get("current_price", 0.0))
    if cur_price <= 0.0:
        hist = get_price_history(target_symbol, period="1mo")
        if hist is not None and not hist.empty:
            cur_price = float(hist["Close"].iloc[-1])
        else:
            cur_price = 100.0

    hist_data = get_price_history(target_symbol, period="6mo")

    res = run_monte_carlo_simulation(
        symbol=target_symbol,
        current_price=cur_price,
        df=hist_data,
        simulations=simulations,
        forecast_days=days,
        tp1=tp1,
        stop_loss=stop_loss,
    )
    return sanitize_json(asdict(res))
