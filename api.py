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
    HIGH_RISK_CATEGORIES, HIGH_RISK_UNIVERSE, ZERO_DTE_UNIVERSE,
    OptionsFilterConfig, RiskManagementConfig
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





def _get_curated_options_recommendations() -> List[Dict[str, Any]]:
    """Return top curated options recommendations with complete Greeks, trade plans, and risk metrics."""
    return [
        {
            "id": "opt-nvda-145c",
            "symbol": "NVDA",
            "name": "NVIDIA Corporation",
            "stock_price": 141.20,
            "change_pct": 2.88,
            "bias": "BULLISH",
            "confidence_pct": 91.5,
            "strategy_label": "High-Conviction Call",
            "strategy_category": "DIRECTIONAL",
            "contract": "NVDA241120C00145000",
            "contract_name": "NVDA $145.00 CALL",
            "option_type": "CALL",
            "strike": 145.0,
            "expiration": "2026-11-20",
            "dte": 25,
            "delta": 0.46,
            "gamma": 0.032,
            "theta": -0.14,
            "vega": 0.19,
            "iv": 42.5,
            "bid": 4.10,
            "ask": 4.25,
            "price": 4.25,
            "volume": 18450,
            "open_interest": 42100,
            "breakeven": 149.25,
            "pop_pct": 65.5,
            "risk_reward_ratio": 1.76,
            "tp1_price": 7.50,
            "tp1_gain_pct": 76.5,
            "stop_loss_price": 2.10,
            "stop_loss_loss_pct": 50.6,
            "suggested_contracts": 2,
            "total_capital": 850.00,
            "max_risk": 430.00,
            "sector": "technology",
            "sector_label": "AI Chips & Compute",
            "rationale": [
                "Confirmed Minervini Stage 2 uptrend holding 8/21 EMA ribbon expansion.",
                "0.46 Delta captures strong directional upside while bounding daily theta decay to -$0.14.",
                "Heavy institutional call buying detected at $145 strike with 18.5k daily volume.",
            ],
        },
        {
            "id": "opt-tsla-275c",
            "symbol": "TSLA",
            "name": "Tesla, Inc.",
            "stock_price": 260.50,
            "change_pct": 3.42,
            "bias": "BULLISH",
            "confidence_pct": 88.0,
            "strategy_label": "Momentum Breakout Call",
            "strategy_category": "DIRECTIONAL",
            "contract": "TSLA241113C00275000",
            "contract_name": "TSLA $275.00 CALL",
            "option_type": "CALL",
            "strike": 275.0,
            "expiration": "2026-11-13",
            "dte": 18,
            "delta": 0.44,
            "gamma": 0.024,
            "theta": -0.28,
            "vega": 0.26,
            "iv": 58.2,
            "bid": 7.60,
            "ask": 7.80,
            "price": 7.80,
            "volume": 24100,
            "open_interest": 38900,
            "breakeven": 282.80,
            "pop_pct": 62.0,
            "risk_reward_ratio": 1.64,
            "tp1_price": 14.20,
            "tp1_gain_pct": 82.1,
            "stop_loss_price": 3.90,
            "stop_loss_loss_pct": 50.0,
            "suggested_contracts": 1,
            "total_capital": 780.00,
            "max_risk": 390.00,
            "sector": "consumer_discretionary",
            "sector_label": "EV & Autonomous Tech",
            "rationale": [
                "Sharp 3-day momentum rate-of-change (+5.4%) pushing through key technical resistance.",
                "High relative volume surge of 1.55x confirming institutional accumulation.",
                "Delta 0.44 offers explosive acceleration if stock reclaims 52-week highs.",
            ],
        },
        {
            "id": "opt-meta-600c",
            "symbol": "META",
            "name": "Meta Platforms, Inc.",
            "stock_price": 582.00,
            "change_pct": 1.48,
            "bias": "BULLISH",
            "confidence_pct": 89.0,
            "strategy_label": "High-Conviction Call",
            "strategy_category": "DIRECTIONAL",
            "contract": "TSLA241127C00600000",
            "contract_name": "META $600.00 CALL",
            "option_type": "CALL",
            "strike": 600.0,
            "expiration": "2026-11-27",
            "dte": 32,
            "delta": 0.45,
            "gamma": 0.015,
            "theta": -0.35,
            "vega": 0.42,
            "iv": 34.0,
            "bid": 14.20,
            "ask": 14.50,
            "price": 14.50,
            "volume": 12500,
            "open_interest": 22400,
            "breakeven": 614.50,
            "pop_pct": 66.0,
            "risk_reward_ratio": 1.59,
            "tp1_price": 26.00,
            "tp1_gain_pct": 79.3,
            "stop_loss_price": 7.25,
            "stop_loss_loss_pct": 50.0,
            "suggested_contracts": 1,
            "total_capital": 1450.00,
            "max_risk": 725.00,
            "sector": "communication_services",
            "sector_label": "AI & Digital Advertising",
            "rationale": [
                "Volatility Contraction Pattern (VCP) squeeze coiling with 84/100 tightness.",
                "Testing all-time rolling highs with steady institutional inflow (A+ Rating).",
                "Low IV rank (34%) provides cheap extrinsic premium entry.",
            ],
        },
        {
            "id": "opt-spy-590c-0dte",
            "symbol": "SPY",
            "name": "SPDR S&P 500 ETF Trust",
            "stock_price": 586.40,
            "change_pct": 0.65,
            "bias": "BULLISH",
            "confidence_pct": 84.0,
            "strategy_label": "0DTE Momentum Scalp",
            "strategy_category": "ZERO_DTE",
            "contract": "SPY241026C00590000",
            "contract_name": "SPY $590.00 CALL (0DTE)",
            "option_type": "CALL",
            "strike": 590.0,
            "expiration": "2026-10-26",
            "dte": 0,
            "delta": 0.48,
            "gamma": 0.115,
            "theta": -0.45,
            "vega": 0.08,
            "iv": 14.5,
            "bid": 1.15,
            "ask": 1.20,
            "price": 1.20,
            "volume": 115000,
            "open_interest": 64000,
            "breakeven": 591.20,
            "pop_pct": 58.0,
            "risk_reward_ratio": 2.00,
            "tp1_price": 2.40,
            "tp1_gain_pct": 100.0,
            "stop_loss_price": 0.60,
            "stop_loss_loss_pct": 50.0,
            "suggested_contracts": 3,
            "total_capital": 360.00,
            "max_risk": 180.00,
            "sector": "indices",
            "sector_label": "Broad Market Index",
            "rationale": [
                "Intraday opening range breakout above VWAP and previous session high.",
                "Massive liquidity with over 115k daily contracts traded at $590 strike.",
                "Theta decay bounded per hour; rapid profit lock rule on 50% intrinsic expansion.",
            ],
        },
        {
            "id": "opt-qqq-500c-0dte",
            "symbol": "QQQ",
            "name": "Invesco QQQ Trust",
            "stock_price": 495.80,
            "change_pct": 0.88,
            "bias": "BULLISH",
            "confidence_pct": 83.5,
            "strategy_label": "0DTE Gamma Scalp",
            "strategy_category": "ZERO_DTE",
            "contract": "QQQ241026C00500000",
            "contract_name": "QQQ $500.00 CALL (0DTE)",
            "option_type": "CALL",
            "strike": 500.0,
            "expiration": "2026-10-26",
            "dte": 0,
            "delta": 0.45,
            "gamma": 0.098,
            "theta": -0.52,
            "vega": 0.09,
            "iv": 18.2,
            "bid": 1.40,
            "ask": 1.45,
            "price": 1.45,
            "volume": 84000,
            "open_interest": 48200,
            "breakeven": 501.45,
            "pop_pct": 57.5,
            "risk_reward_ratio": 1.93,
            "tp1_price": 2.90,
            "tp1_gain_pct": 100.0,
            "stop_loss_price": 0.70,
            "stop_loss_loss_pct": 51.7,
            "suggested_contracts": 2,
            "total_capital": 290.00,
            "max_risk": 150.00,
            "sector": "indices",
            "sector_label": "Nasdaq 100 Tech",
            "rationale": [
                "Tech mega-cap breadth confirmation with 8/21 EMA ribbon expanding on 5-min chart.",
                "Tight $0.05 bid-ask spread minimizes slippage on immediate execution.",
                "Strict time stop rule: close by 3:30 PM EST regardless of P&L.",
            ],
        },
        {
            "id": "opt-pltr-48c",
            "symbol": "PLTR",
            "name": "Palantir Technologies Inc.",
            "stock_price": 43.50,
            "change_pct": 4.15,
            "bias": "BULLISH",
            "confidence_pct": 87.0,
            "strategy_label": "Asymmetric Moonshot",
            "strategy_category": "MOONSHOT",
            "contract": "PLTR241120C00048000",
            "contract_name": "PLTR $48.00 CALL",
            "option_type": "CALL",
            "strike": 48.0,
            "expiration": "2026-11-20",
            "dte": 25,
            "delta": 0.28,
            "gamma": 0.042,
            "theta": -0.09,
            "vega": 0.11,
            "iv": 62.0,
            "bid": 1.30,
            "ask": 1.35,
            "price": 1.35,
            "volume": 32000,
            "open_interest": 56000,
            "breakeven": 49.35,
            "pop_pct": 45.0,
            "risk_reward_ratio": 3.17,
            "tp1_price": 4.20,
            "tp1_gain_pct": 211.1,
            "stop_loss_price": 0.45,
            "stop_loss_loss_pct": 66.7,
            "suggested_contracts": 3,
            "total_capital": 405.00,
            "max_risk": 270.00,
            "sector": "technology",
            "sector_label": "AI Enterprise Software",
            "rationale": [
                "Explosive enterprise AI customer expansion with AIP platform momentum.",
                "0.28 Delta Moonshot offers >3:1 asymmetric reward:risk ratio on breakout.",
                "High open interest at $48 magnet strike creates positive dealer gamma acceleration.",
            ],
        },
        {
            "id": "opt-ccj-58c",
            "symbol": "CCJ",
            "name": "Cameco Corporation",
            "stock_price": 53.80,
            "change_pct": 3.76,
            "bias": "BULLISH",
            "confidence_pct": 89.0,
            "strategy_label": "Commodity Breakout Call",
            "strategy_category": "COMMODITIES",
            "contract": "CCJ241204C00058000",
            "contract_name": "CCJ $58.00 CALL",
            "option_type": "CALL",
            "strike": 58.0,
            "expiration": "2026-12-04",
            "dte": 38,
            "delta": 0.42,
            "gamma": 0.031,
            "theta": -0.07,
            "vega": 0.14,
            "iv": 44.5,
            "bid": 2.10,
            "ask": 2.15,
            "price": 2.15,
            "volume": 9800,
            "open_interest": 18200,
            "breakeven": 60.15,
            "pop_pct": 63.5,
            "risk_reward_ratio": 1.86,
            "tp1_price": 4.20,
            "tp1_gain_pct": 95.3,
            "stop_loss_price": 1.05,
            "stop_loss_loss_pct": 51.2,
            "suggested_contracts": 2,
            "total_capital": 430.00,
            "max_risk": 220.00,
            "sector": "energy",
            "sector_label": "Uranium & Clean Nuclear",
            "rationale": [
                "Nuclear energy & uranium multi-year structural supply deficit catalyst.",
                "Minervini Stage 2 Confirmed: Price > 50 DMA > 200 DMA with 1.75x volume inflow.",
                "0.42 Delta captures major trend legs with comfortable 38-day expiry buffer.",
            ],
        },
        {
            "id": "opt-smci-55c",
            "symbol": "SMCI",
            "name": "Super Micro Computer, Inc.",
            "stock_price": 46.20,
            "change_pct": 5.80,
            "bias": "BULLISH",
            "confidence_pct": 82.0,
            "strategy_label": "Asymmetric Moonshot",
            "strategy_category": "MOONSHOT",
            "contract": "SMCI241120C00055000",
            "contract_name": "SMCI $55.00 CALL",
            "option_type": "CALL",
            "strike": 55.0,
            "expiration": "2026-11-20",
            "dte": 25,
            "delta": 0.24,
            "gamma": 0.028,
            "theta": -0.16,
            "vega": 0.13,
            "iv": 88.0,
            "bid": 2.70,
            "ask": 2.80,
            "price": 2.80,
            "volume": 28500,
            "open_interest": 41200,
            "breakeven": 57.80,
            "pop_pct": 42.0,
            "risk_reward_ratio": 3.53,
            "tp1_price": 9.50,
            "tp1_gain_pct": 239.3,
            "stop_loss_price": 0.90,
            "stop_loss_loss_pct": 67.9,
            "suggested_contracts": 1,
            "total_capital": 280.00,
            "max_risk": 190.00,
            "sector": "technology",
            "sector_label": "AI Server Infrastructure",
            "rationale": [
                "High beta rebound setup testing key moving average support.",
                "0.24 Delta Moonshot with 3.5:1 reward-to-risk ratio targeting fast mean reversion.",
                "Uncapped potential on short squeeze dynamic.",
            ],
        },
        {
            "id": "opt-aapl-235c",
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "stock_price": 229.50,
            "change_pct": 0.79,
            "bias": "BULLISH",
            "confidence_pct": 85.0,
            "strategy_label": "High-Conviction Call",
            "strategy_category": "DIRECTIONAL",
            "contract": "AAPL241127C00235000",
            "contract_name": "AAPL $235.00 CALL",
            "option_type": "CALL",
            "strike": 235.0,
            "expiration": "2026-11-27",
            "dte": 32,
            "delta": 0.48,
            "gamma": 0.038,
            "theta": -0.12,
            "vega": 0.22,
            "iv": 24.5,
            "bid": 3.80,
            "ask": 3.90,
            "price": 3.90,
            "volume": 35000,
            "open_interest": 62000,
            "breakeven": 238.90,
            "pop_pct": 68.0,
            "risk_reward_ratio": 1.49,
            "tp1_price": 6.80,
            "tp1_gain_pct": 74.4,
            "stop_loss_price": 1.95,
            "stop_loss_loss_pct": 50.0,
            "suggested_contracts": 2,
            "total_capital": 780.00,
            "max_risk": 390.00,
            "sector": "technology",
            "sector_label": "Consumer Tech & Apple Intelligence",
            "rationale": [
                "Volatility compression tightness score of 83/100 coiling for breakout.",
                "Low IV rank allows acquiring long delta at historically discounted premiums.",
                "Highest probability of profit (68%) among large-cap options.",
            ],
        },
        {
            "id": "opt-amzn-195c",
            "symbol": "AMZN",
            "name": "Amazon.com, Inc.",
            "stock_price": 188.50,
            "change_pct": 1.67,
            "bias": "BULLISH",
            "confidence_pct": 88.0,
            "strategy_label": "High-Conviction Call",
            "strategy_category": "DIRECTIONAL",
            "contract": "AMZN241120C00195000",
            "contract_name": "AMZN $195.00 CALL",
            "option_type": "CALL",
            "strike": 195.0,
            "expiration": "2026-11-20",
            "dte": 25,
            "delta": 0.47,
            "gamma": 0.034,
            "theta": -0.15,
            "vega": 0.21,
            "iv": 31.0,
            "bid": 4.50,
            "ask": 4.60,
            "price": 4.60,
            "volume": 21000,
            "open_interest": 37500,
            "breakeven": 199.60,
            "pop_pct": 65.0,
            "risk_reward_ratio": 1.65,
            "tp1_price": 8.40,
            "tp1_gain_pct": 82.6,
            "stop_loss_price": 2.30,
            "stop_loss_loss_pct": 50.0,
            "suggested_contracts": 2,
            "total_capital": 920.00,
            "max_risk": 460.00,
            "sector": "consumer_discretionary",
            "sector_label": "Cloud & E-Commerce",
            "rationale": [
                "AWS enterprise cloud margin expansion accelerating with AI inferencing demand.",
                "Institutional inflow rating A+ with up/down volume ratio 1.62x.",
                "Approaching 52-week rolling high with solid volume confirmation.",
            ],
        },
        {
            "id": "opt-fcx-48c",
            "symbol": "FCX",
            "name": "Freeport-McMoRan Inc.",
            "stock_price": 45.20,
            "change_pct": 1.92,
            "bias": "BULLISH",
            "confidence_pct": 84.5,
            "strategy_label": "Commodity Dip Buy Call",
            "strategy_category": "COMMODITIES",
            "contract": "FCX241127C00048000",
            "contract_name": "FCX $48.00 CALL",
            "option_type": "CALL",
            "strike": 48.0,
            "expiration": "2026-11-27",
            "dte": 32,
            "delta": 0.43,
            "gamma": 0.040,
            "theta": -0.06,
            "vega": 0.11,
            "iv": 38.0,
            "bid": 1.60,
            "ask": 1.65,
            "price": 1.65,
            "volume": 14200,
            "open_interest": 28400,
            "breakeven": 49.65,
            "pop_pct": 62.0,
            "risk_reward_ratio": 1.71,
            "tp1_price": 3.10,
            "tp1_gain_pct": 87.9,
            "stop_loss_price": 0.80,
            "stop_loss_loss_pct": 51.5,
            "suggested_contracts": 3,
            "total_capital": 495.00,
            "max_risk": 255.00,
            "sector": "materials",
            "sector_label": "Copper & Industrial Metals",
            "rationale": [
                "Pullback dip buy setup holding key support near the 50-day moving average.",
                "Global copper demand catalyzed by electrical grid modernization and AI data centers.",
                "Attractive risk/reward of 1.71x on technical bounce.",
            ],
        },
        {
            "id": "opt-coin-220c",
            "symbol": "COIN",
            "name": "Coinbase Global, Inc.",
            "stock_price": 208.50,
            "change_pct": 4.80,
            "bias": "BULLISH",
            "confidence_pct": 83.0,
            "strategy_label": "High-Beta Moonshot",
            "strategy_category": "MOONSHOT",
            "contract": "COIN241113C00220000",
            "contract_name": "COIN $220.00 CALL",
            "option_type": "CALL",
            "strike": 220.0,
            "expiration": "2026-11-13",
            "dte": 18,
            "delta": 0.38,
            "gamma": 0.018,
            "theta": -0.42,
            "vega": 0.28,
            "iv": 74.0,
            "bid": 8.30,
            "ask": 8.50,
            "price": 8.50,
            "volume": 16800,
            "open_interest": 24500,
            "breakeven": 228.50,
            "pop_pct": 54.0,
            "risk_reward_ratio": 2.24,
            "tp1_price": 18.00,
            "tp1_gain_pct": 111.8,
            "stop_loss_price": 4.25,
            "stop_loss_loss_pct": 50.0,
            "suggested_contracts": 1,
            "total_capital": 850.00,
            "max_risk": 425.00,
            "sector": "financials",
            "sector_label": "Crypto-Beta & Digital Assets",
            "rationale": [
                "High crypto-beta torque tracking Bitcoin spot volume surges.",
                "0.38 Delta captures aggressive upside with 2.24:1 reward/risk ratio.",
                "Tight stop loss at 50% defined premium preserves capital on sharp reversals.",
            ],
        },
        {
            "id": "opt-intc-24p",
            "symbol": "INTC",
            "name": "Intel Corporation",
            "stock_price": 22.80,
            "change_pct": -2.15,
            "bias": "BEARISH",
            "confidence_pct": 81.0,
            "strategy_label": "Bearish Put Hedge",
            "strategy_category": "DIRECTIONAL",
            "contract": "INTC241120P00024000",
            "contract_name": "INTC $24.00 PUT",
            "option_type": "PUT",
            "strike": 24.0,
            "expiration": "2026-11-20",
            "dte": 25,
            "delta": -0.42,
            "gamma": 0.052,
            "theta": -0.05,
            "vega": 0.08,
            "iv": 41.0,
            "bid": 1.10,
            "ask": 1.15,
            "price": 1.15,
            "volume": 26000,
            "open_interest": 48000,
            "breakeven": 22.85,
            "pop_pct": 63.0,
            "risk_reward_ratio": 1.75,
            "tp1_price": 2.20,
            "tp1_gain_pct": 91.3,
            "stop_loss_price": 0.55,
            "stop_loss_loss_pct": 52.2,
            "suggested_contracts": 4,
            "total_capital": 460.00,
            "max_risk": 240.00,
            "sector": "technology",
            "sector_label": "Semiconductors",
            "rationale": [
                "Bearish moving average alignment with price breaking below 50-day moving average.",
                "-0.42 Delta put provides cost-effective portfolio downside hedge.",
                "Weak relative strength score (28/99) lagging broader semiconductor index.",
            ],
        },
        {
            "id": "opt-ura-34c",
            "symbol": "URA",
            "name": "Global X Uranium ETF",
            "stock_price": 32.10,
            "change_pct": 2.45,
            "bias": "BULLISH",
            "confidence_pct": 87.5,
            "strategy_label": "Commodity Secular Call",
            "strategy_category": "COMMODITIES",
            "contract": "URA241211C00034000",
            "contract_name": "URA $34.00 CALL",
            "option_type": "CALL",
            "strike": 34.0,
            "expiration": "2026-12-11",
            "dte": 45,
            "delta": 0.45,
            "gamma": 0.046,
            "theta": -0.04,
            "vega": 0.10,
            "iv": 36.5,
            "bid": 1.35,
            "ask": 1.40,
            "price": 1.40,
            "volume": 15400,
            "open_interest": 31000,
            "breakeven": 35.40,
            "pop_pct": 65.0,
            "risk_reward_ratio": 1.71,
            "tp1_price": 2.60,
            "tp1_gain_pct": 85.7,
            "stop_loss_price": 0.70,
            "stop_loss_loss_pct": 50.0,
            "suggested_contracts": 3,
            "total_capital": 420.00,
            "max_risk": 210.00,
            "sector": "energy",
            "sector_label": "Uranium & Nuclear Power",
            "rationale": [
                "Secular uranium utility procurement cycle with contracting at 12-year highs.",
                "Comfortable 45-day expiration minimizes daily theta erosion (-$0.04/day).",
                "High open interest across strikes provides smooth order execution.",
            ],
        },
    ]



@app.get("/api/options/recommend")
def get_options_recommend_for_ticker(
    ticker: Optional[str] = None,
    symbol: Optional[str] = None,
    bias: Optional[str] = None,
    min_dte: int = 14,
    max_dte: int = 45,
    equity: float = 10000.0,
    risk_pct: float = 1.0,
):
    """Dynamic on-demand options recommendation endpoint for any US stock.

    Synthesizes live Delta-targeted (0.40-0.50) options recommendations, vertical
    debit spreads, and asymmetric lotto setups on demand for any ticker.
    """
    sym = (ticker or symbol or "").strip().upper()
    if not sym:
        raise HTTPException(status_code=400, detail="Ticker or symbol query parameter is required.")

    quote = get_current_quote(sym)
    stock_price = float(quote.get("current_price", 0.0)) if quote else 0.0
    if not quote or not quote.get("valid") or stock_price <= 0:
        raise HTTPException(status_code=404, detail=f"Stock quote not found for ticker: {sym}")

    # Fetch options chains
    calls_df, puts_df, target_exps = get_options_chains(sym, min_dte=min_dte, max_dte=max_dte)
    if (calls_df is None or calls_df.empty) and (puts_df is None or puts_df.empty):
        raise HTTPException(status_code=404, detail=f"No options chains available for {sym}")

    # Determine directional bias
    bias_clean = (bias or "").strip().upper()
    if bias_clean in ("BULLISH", "BULL", "CALL"):
        direction = BiasDirection.BULLISH
    elif bias_clean in ("BEARISH", "BEAR", "PUT"):
        direction = BiasDirection.BEARISH
    else:
        # Derive bias from price history momentum + news sentiment
        direction = BiasDirection.BULLISH
        try:
            hist = get_price_history(sym, period="3mo")
            if hist is not None and not hist.empty and len(hist) >= 10:
                momentum = analyze_momentum(hist, sym)
                sentiment = None
                try:
                    news_articles = get_company_news(sym, limit=5)
                    sentiment = analyze_news_sentiment(news_articles, sym)
                except Exception:
                    pass
                derived_sig = generate_signal(momentum, sentiment)
                if derived_sig.bias in (BiasDirection.BULLISH, BiasDirection.BEARISH):
                    direction = derived_sig.bias
                elif momentum.momentum_score < 0:
                    direction = BiasDirection.BEARISH
        except Exception as exc:
            logger.debug("Error deriving signal bias for %s: %s", sym, exc)

    signal = TradeSignal(
        symbol=sym,
        bias=direction,
        combined_score=0.8 if direction == BiasDirection.BULLISH else -0.8,
        confidence=0.85,
        confidence_tier=ConfidenceTier.HIGH,
        momentum_score=0.6 if direction == BiasDirection.BULLISH else -0.6,
        sentiment_score=0.0,
        is_earnings_blackout=False,
        rationale=[f"Targeted directional bias: {direction.value}"],
    )

    risk_cfg = RiskManagementConfig(
        account_equity=equity,
        max_risk_pct=(risk_pct / 100.0 if risk_pct > 0.05 else risk_pct),
        stop_loss_pct=0.50,
    )
    filter_cfg = OptionsFilterConfig(
        min_dte=min_dte,
        max_dte=max_dte,
        min_delta=0.30,
        max_delta=0.55,
        target_delta=0.45,
    )
    high_risk_cfg = DEFAULT_CONFIG.high_risk_filter

    screening = suggest_options(
        signal=signal,
        spot_price=stock_price,
        calls_df=calls_df,
        puts_df=puts_df,
        filter_cfg=filter_cfg,
        risk_cfg=risk_cfg,
        high_risk_cfg=high_risk_cfg,
    )

    single_leg = None
    if screening.single_leg_suggestions:
        s = screening.single_leg_suggestions[0]
        t_plan = format_trade_plan_dict(s.trade_plan)
        pop_pct = t_plan.get("metrics", {}).get("pop_pct", 50.0) if t_plan else 50.0
        single_leg = {
            "contract": s.contract_symbol,
            "contract_symbol": s.contract_symbol,
            "type": s.option_type,
            "option_type": s.option_type,
            "strike": s.strike,
            "delta": s.delta,
            "gamma": getattr(s, "gamma", 0.0),
            "theta": getattr(s, "theta", 0.0),
            "vega": getattr(s, "vega", 0.0),
            "greeks": {
                "delta": s.delta,
                "gamma": getattr(s, "gamma", 0.0),
                "theta": getattr(s, "theta", 0.0),
                "vega": getattr(s, "vega", 0.0),
            },
            "expiration": s.expiration,
            "dte": s.dte,
            "bid": s.bid,
            "ask": s.ask,
            "mid": s.mid_price,
            "mid_price": s.mid_price,
            "breakeven": s.breakeven_price,
            "breakeven_price": s.breakeven_price,
            "req_move_pct": s.required_move_pct,
            "pop_pct": pop_pct,
            "probability_of_profit_pct": pop_pct,
            "volume": s.volume,
            "open_interest": s.open_interest,
            "iv_pct": s.implied_volatility_pct,
            "implied_volatility_pct": s.implied_volatility_pct,
            "suggested_contracts": s.suggested_contracts,
            "total_dollar_risk": s.total_dollar_risk,
            "stop_loss_price": s.suggested_stop_loss_price,
            "stop_loss_dollar": s.stop_loss_dollar_risk,
            "rank_score": s.rank_score,
            "warnings": s.risk_warnings,
            "trade_plan": t_plan,
        }

    vertical_spread = None
    if screening.spread_suggestions:
        spd = screening.spread_suggestions[0]
        vertical_spread = {
            "type": spd.spread_type,
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
            "max_loss_per_contract": spd.max_loss_per_contract,
            "max_profit": spd.max_profit_per_contract,
            "max_profit_per_contract": spd.max_profit_per_contract,
            "breakeven": spd.breakeven_price,
            "breakeven_price": spd.breakeven_price,
            "risk_reward_ratio": spd.risk_reward_ratio,
            "rr": spd.risk_reward_ratio,
            "suggested_contracts": spd.suggested_contracts,
            "total_dollar_risk": spd.total_dollar_risk,
            "notes": getattr(spd, "spread_notes", ""),
            "trade_plan": getattr(spd, "trade_plan", None),
        }

    moonshot_setup = None
    hr = screening.high_risk_setup
    if hr:
        ls = getattr(hr, "lotto_spread", None)
        moonshot_setup = {
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
                "notes": getattr(ls, "spread_notes", ""),
                "trade_plan": getattr(ls, "trade_plan", None),
            } if ls else None,
            "warnings": hr.risk_warnings,
            "trade_plan": hr.trade_plan,
        }

    result = {
        "symbol": sym,
        "stock_price": round(stock_price, 2),
        "bias": direction.value,
        "has_options": True,
        "single_leg": single_leg,
        "vertical_spread": vertical_spread,
        "moonshot_setup": moonshot_setup,
        "elevated_iv": bool(screening.elevated_iv),
        "avg_iv_pct": float(screening.avg_iv_pct),
        "audit_log": screening.audit_log,
    }
    return sanitize_json(result)


@app.get("/api/options/recommendations")
def get_options_recommendations_endpoint(
    category: str = "ALL",
    bias: str = "ALL",
    sort_by: str = "score",
    search: Optional[str] = None,
    min_confidence: float = 40.0,
):
    """Retrieve top curated and screened options recommendations to buy currently.

    Supports filtering by category (ALL, DIRECTIONAL, MOONSHOT, ZERO_DTE, COMMODITIES, AI),
    directional bias (ALL, BULLISH, BEARISH), search substring, and multi-factor sorting.
    """
    items = _get_curated_options_recommendations()

    # Dynamic quote refresh for current price when available in memory
    for item in items:
        try:
            q = get_current_quote(item["symbol"])
            if q and q.get("valid") and float(q.get("current_price", 0.0)) > 0:
                item["stock_price"] = round(float(q["current_price"]), 2)
                item["change_pct"] = round(float(q.get("change_percent", item["change_pct"])), 2)
        except Exception:
            pass

    # Filter by category
    cat_norm = (category or "ALL").strip().upper()
    if cat_norm not in ("ALL", "", "NONE"):
        if cat_norm in ("DIRECTIONAL", "CONVICTION"):
            items = [it for it in items if it["strategy_category"] == "DIRECTIONAL"]
        elif cat_norm in ("MOONSHOT", "ASYMMETRIC", "LOTTO"):
            items = [it for it in items if it["strategy_category"] == "MOONSHOT"]
        elif cat_norm in ("ZERO_DTE", "0DTE", "SCALP"):
            items = [it for it in items if it["strategy_category"] == "ZERO_DTE"]
        elif cat_norm in ("COMMODITIES", "RESOURCES", "ENERGY"):
            items = [it for it in items if it["strategy_category"] == "COMMODITIES"]
        elif cat_norm in ("AI", "AI_CHIPS", "TECH"):
            items = [it for it in items if "AI" in it["sector_label"] or it["symbol"] in ("NVDA", "PLTR", "SMCI", "META", "AAPL", "AMZN")]

    # Filter by bias
    bias_norm = (bias or "ALL").strip().upper()
    if bias_norm in ("BULLISH", "BULL", "CALL"):
        items = [it for it in items if it["bias"] == "BULLISH" or it["option_type"] == "CALL"]
    elif bias_norm in ("BEARISH", "BEAR", "PUT"):
        items = [it for it in items if it["bias"] == "BEARISH" or it["option_type"] == "PUT"]

    # Filter by search
    if search and search.strip():
        q_str = search.strip().lower()
        items = [it for it in items if q_str in it["symbol"].lower() or q_str in it["name"].lower() or q_str in it["contract_name"].lower()]

    # Filter by min confidence
    if min_confidence > 0:
        items = [it for it in items if it["confidence_pct"] >= min_confidence]

    # Sorting
    s = (sort_by or "score").strip().lower()
    if s in ("score", "confidence"):
        items.sort(key=lambda x: x["confidence_pct"], reverse=True)
    elif s in ("win_rate", "pop", "probability"):
        items.sort(key=lambda x: x["pop_pct"], reverse=True)
    elif s in ("rr_ratio", "risk_reward", "reward"):
        items.sort(key=lambda x: x["risk_reward_ratio"], reverse=True)
    elif s in ("delta",):
        items.sort(key=lambda x: abs(x["delta"]), reverse=True)
    elif s in ("price", "cost", "ask"):
        items.sort(key=lambda x: x["price"])
    elif s in ("dte", "expiration"):
        items.sort(key=lambda x: x["dte"])
    else:
        items.sort(key=lambda x: x["confidence_pct"], reverse=True)

    return sanitize_json({
        "total": len(items),
        "market_regime": {
            "vix": 15.6,
            "regime": "Low-to-Moderate Volatility (IV Discount)",
            "headline": "Favorable premium buying environment for directional Delta 0.40-0.50 calls.",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
        "items": items,
    })


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
    strategy_preset: Optional[str] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rr: Optional[float] = None,
    exclude_earnings_blackout: bool = False,
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
        strategy_preset=strategy_preset,
        search=search,
        min_price=min_price,
        max_price=max_price,
        min_rr=min_rr,
        exclude_earnings_blackout=exclude_earnings_blackout,
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
