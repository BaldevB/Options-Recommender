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
from starlette.concurrency import run_in_threadpool
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
from options.edge import build_market_context
from analysis import rec_journal

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

    journal_stop = threading.Event()
    if os.environ.get("REC_JOURNAL_EVAL_ENABLED", "1").lower() in ("1", "true", "yes"):
        def _journal_loop() -> None:
            if journal_stop.wait(90):  # let the server warm up first
                return
            while not journal_stop.is_set():
                stats = rec_journal.maybe_evaluate(force=True)
                if stats:
                    logger.info("Recommendation journal evaluated: %s", stats)
                if journal_stop.wait(6 * 3600):
                    return

        threading.Thread(target=_journal_loop, name="rec-journal-eval", daemon=True).start()

    yield

    journal_stop.set()
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
            "pop_method": getattr(tp, "pop_method", "risk_neutral_expiry"),
            "prob_target_before_stop_pct": getattr(tp, "prob_target_before_stop_pct", None),
            "prob_stop_first_pct": getattr(tp, "prob_stop_first_pct", None),
            "prob_time_exit_pct": getattr(tp, "prob_time_exit_pct", None),
            "expected_return_pct": getattr(tp, "expected_return_pct", None),
        },
        "playbook_steps": getattr(tp, "playbook_steps", []),
        "ratchet_ladder": getattr(tp, "ratchet_ladder", []),
        "rolling_playbook": getattr(tp, "rolling_playbook", {}),
        "broker_bracket_order": getattr(tp, "broker_bracket_order", {}),
    }


def _edge_ctx(symbol: str, spot: float, hist: Any, signal: Any, earnings_info: Optional[Dict[str, Any]] = None):
    """Market context for the edge model; None (legacy ranking) if anything goes wrong."""
    try:
        return build_market_context(symbol, spot, hist, signal, earnings_info, DEFAULT_CONFIG.edge)
    except Exception as exc:
        logger.debug("Edge context unavailable for %s: %s", symbol, exc)
        return None


def edge_fields(s: Any) -> Dict[str, Any]:
    """Edge-model fields for a single-leg suggestion (all optional for older clients)."""
    tp = getattr(s, "trade_plan", None)
    pop = getattr(tp, "probability_of_profit_pct", None)
    return {
        "edge_score": getattr(s, "edge_score", None),
        "execution_score": getattr(s, "execution_score", None),
        "iv_source": getattr(s, "iv_source", "yfinance"),
        "iv_hv_ratio": getattr(s, "iv_hv_ratio", None),
        "vol_regime": getattr(s, "vol_regime", "UNKNOWN"),
        "expected_move_pct": getattr(s, "expected_move_pct", None),
        "move_coverage_ratio": getattr(s, "move_coverage_ratio", None),
        "theta_vs_gamma_ratio": getattr(s, "theta_vs_gamma_ratio", None),
        "spans_earnings": bool(getattr(s, "spans_earnings", False)),
        "earnings_date": getattr(s, "earnings_date", None),
        "pop_method": getattr(tp, "pop_method", "risk_neutral_expiry"),
        "prob_target_before_stop_pct": getattr(tp, "prob_target_before_stop_pct", None),
        "expected_return_pct": getattr(tp, "expected_return_pct", None),
        # Realized win rate of past ideas with a similar predicted probability (None until enough history)
        "calibrated_win_rate_pct": rec_journal.calibrated_win_rate(pop),
    }


def _journal_screening(screening: Any, symbol: str, signal: Any, source: str, top_n: int = 1) -> None:
    """Record the top suggestion(s) so their outcomes can be scored later. Never raises."""
    try:
        bias = getattr(getattr(signal, "bias", None), "value", "")
        conf = float(getattr(signal, "confidence", 0.0) or 0.0)
        items = [
            rec_journal.suggestion_to_journal_item(sug, symbol, bias, conf)
            for sug in (screening.single_leg_suggestions or [])[:top_n]
        ]
        rec_journal.record_recommendations(items, source=source)
    except Exception as exc:
        logger.debug("Journal record skipped for %s: %s", symbol, exc)


@app.get("/api/calibration")
def get_calibration_endpoint(evaluate: bool = False):
    """How accurate have past recommendations been? Optionally scores pending ones first."""
    eval_stats = rec_journal.maybe_evaluate(force=evaluate)
    report = rec_journal.calibration_report()
    report["last_evaluation"] = eval_stats
    return sanitize_json(report)


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
    if momentum is None:
        raise HTTPException(status_code=422, detail=f"Not enough price history to analyze {ticker}")
    news_articles = get_company_news(ticker, limit=cfg.news_limit)
    sentiment = analyze_news_sentiment(news_articles, ticker)
    signal = generate_signal(momentum, sentiment, earnings_info, cfg.weights, cfg.earnings)

    # Options chain screening (disciplined + high-risk asymmetric)
    calls_df, puts_df, _ = get_options_chains(ticker, cfg.options_filter.min_dte, cfg.options_filter.max_dte)
    screening = suggest_options(
        signal, quote["current_price"], calls_df, puts_df,
        cfg.options_filter, cfg.risk, cfg.high_risk_filter,
        market_ctx=_edge_ctx(ticker, quote["current_price"], hist, signal, earnings_info),
    )
    _journal_screening(screening, ticker, signal, "stock-analysis")

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
                    **edge_fields(s),
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
            "iv_hv_ratio": screening.iv_hv_ratio,
            "vol_regime": screening.vol_regime,
            "realized_vol_pct": screening.realized_vol_pct,
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
                cfg.options_filter, cfg.risk, cfg.high_risk_filter,
                market_ctx=_edge_ctx(sym, quote["current_price"], hist, sig, e_info),
            )
            _journal_screening(screening, sym, sig, "high-confidence")

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
                sig.bias = BiasDirection.BULLISH if mom.momentum_score >= 0 else BiasDirection.BEARISH
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
                bias = BiasDirection.BULLISH if mom.momentum_score >= 0 else BiasDirection.BEARISH

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






# In-memory bounded cache for live options recommendations
_LIVE_OPTIONS_CACHE: Dict[str, Any] = {
    "timestamp": 0.0,
    "items": [],
}
LIVE_OPTIONS_CACHE_TTL = 300.0  # 5 minutes cache TTL
# Outcome of the most recent live screen, shown to the user so an empty list is explained
_LIVE_OPTIONS_STATUS: Dict[str, Any] = {"state": "unknown", "checked_at": 0.0, "symbols_screened": 0, "message": ""}


def _get_live_options_recommendations(force: bool = False) -> List[Dict[str, Any]]:
    """Retrieve genuinely screened live options recommendations with strict delta targeting and Greeks.

    Screens contracts from top stocks in screener cache or top liquid benchmark equities.
    Returns honest empty list if no contracts qualify or market data is unavailable.
    """
    import time
    global _LIVE_OPTIONS_CACHE
    now = time.time()
    if not force and _LIVE_OPTIONS_CACHE["items"] and (now - _LIVE_OPTIONS_CACHE["timestamp"] < LIVE_OPTIONS_CACHE_TTL):
        return _LIVE_OPTIONS_CACHE["items"]
    if not force and _LIVE_OPTIONS_STATUS.get("state") == "empty" and now - _LIVE_OPTIONS_STATUS.get("checked_at", 0.0) < 60.0:
        return []

    candidates: List[Dict[str, Any]] = []

    # Priority 1: Screened stocks from screener cache
    screener_res = None
    try:
        cache = get_screener_cache()
        screener_res = cache.get_recommendations(limit=8)
    except Exception as exc:
        logger.debug("Screener cache lookup failed: %s", exc)

    screener_items = screener_res.get("items", []) if isinstance(screener_res, dict) else (screener_res or [])
    symbols_to_screen = []
    if screener_items:
        for it in screener_items:
            if isinstance(it, dict):
                symbols_to_screen.append((it.get("symbol"), it.get("name", it.get("symbol")), it.get("sector", "general"), it.get("score", 75.0), it.get("action", "BUY")))
            else:
                symbols_to_screen.append((getattr(it, "symbol", ""), getattr(it, "name", ""), getattr(it, "sector", "general"), getattr(it, "score", 75.0), getattr(it, "action", "BUY")))
        # HOLD / AVOID / EARNINGS BLACKOUT rows must not be turned into directional option trades
        symbols_to_screen = [row for row in symbols_to_screen if "BUY" in str(row[4]).upper()]
    if not symbols_to_screen:
        # Benchmark liquid equities
        fallback_tickers = [
            ("NVDA", "NVIDIA Corporation", "technology", 88.0, "STRONG BUY"),
            ("AAPL", "Apple Inc.", "technology", 80.0, "BUY"),
            ("MSFT", "Microsoft Corporation", "technology", 78.0, "BUY"),
            ("AMZN", "Amazon.com Inc.", "consumer_discretionary", 76.0, "BUY"),
            ("META", "Meta Platforms Inc.", "technology", 82.0, "STRONG BUY"),
            ("TSLA", "Tesla Inc.", "consumer_discretionary", 75.0, "BUY"),
        ]
        symbols_to_screen = fallback_tickers

    cfg = DEFAULT_CONFIG

    for sym, name, sector, score, action in symbols_to_screen[:6]:
        try:
            q = get_current_quote(sym)
            if not q or not q.get("valid") or float(q.get("current_price", 0.0)) <= 0:
                continue
            spot = float(q["current_price"])
            change_p = float(q.get("change_percent", 0.0))

            calls_df, puts_df, target_exps = get_options_chains(sym, min_dte=14, max_dte=45)
            if (calls_df is None or calls_df.empty) and (puts_df is None or puts_df.empty):
                continue

            # Determine bias
            bias = BiasDirection.BULLISH if "BUY" in str(action).upper() else BiasDirection.BEARISH
            conf = min(0.95, max(0.40, float(score) / 100.0))

            signal = TradeSignal(
                symbol=sym,
                bias=bias,
                combined_score=conf if bias == BiasDirection.BULLISH else -conf,
                confidence=conf,
                confidence_tier=ConfidenceTier.HIGH if conf >= 0.75 else ConfidenceTier.MEDIUM,
                momentum_score=conf * 100.0,
                sentiment_score=0.20,
                is_earnings_blackout=False,
                rationale=[f"Algorithmic technical score: {score:.1f}/100"],
            )

            live_hist = get_price_history(sym, period="6mo")
            live_earn = get_earnings_info(sym, cfg.earnings.blackout_days, cfg.earnings.warning_days)
            screening = suggest_options(
                signal, spot, calls_df, puts_df,
                cfg.options_filter, cfg.risk, cfg.high_risk_filter,
                market_ctx=_edge_ctx(sym, spot, live_hist, signal, live_earn),
            )
            _journal_screening(screening, sym, signal, "live-feed")

            if screening.single_leg_suggestions:
                best = screening.single_leg_suggestions[0]
                spd = screening.spread_suggestions[0] if screening.spread_suggestions else None
                rec_id = f"opt-{sym.lower()}-{best.strike:.0f}{best.option_type[0].lower()}"

                # Vertical spread object for card toggle
                v_spread = None
                if spd:
                    v_spread = {
                        "spread_type": "BULL_CALL" if best.option_type == "CALL" else "BEAR_PUT",
                        "spread_label": spd.spread_type,
                        "long_strike": spd.long_strike,
                        "short_strike": spd.short_strike,
                        "long_ask": spd.long_ask,
                        "short_bid": spd.short_bid,
                        "net_debit": spd.net_debit,
                        "max_loss": spd.max_loss_per_contract,
                        "max_profit": spd.max_profit_per_contract,
                        "breakeven": spd.breakeven_price,
                        "rr_ratio": spd.risk_reward_ratio,
                        "width": abs(spd.short_strike - spd.long_strike),
                        "suggested_contracts": spd.suggested_contracts,
                    }

                candidates.append({
                    "id": rec_id,
                    "symbol": sym,
                    "name": name,
                    "stock_price": round(spot, 2),
                    "change_pct": round(change_p, 2),
                    "bias": bias.value,
                    "confidence_pct": round(conf * 100.0, 1),
                    "strategy_label": f"Delta {best.delta:.2f} {best.option_type.capitalize()}",
                    "strategy_category": "DIRECTIONAL",
                    "contract": best.contract_symbol,
                    "contract_name": f"{sym} ${best.strike:.2f} {best.option_type}",
                    "option_type": best.option_type,
                    "strike": best.strike,
                    "expiration": best.expiration,
                    "dte": best.dte,
                    "delta": best.delta,
                    "gamma": best.gamma,
                    "theta": best.theta,
                    "vega": best.vega,
                    "iv": best.implied_volatility_pct,
                    "bid": best.bid,
                    "ask": best.ask,
                    "price": best.ask,
                    "volume": best.volume,
                    "open_interest": best.open_interest,
                    "breakeven": best.breakeven_price,
                    "pop_pct": best.trade_plan.probability_of_profit_pct if best.trade_plan else 50.0,
                    "risk_reward_ratio": best.trade_plan.risk_reward_ratio if best.trade_plan else 2.0,
                    "tp1_price": best.trade_plan.tp1_option_price if best.trade_plan else round(best.ask * 1.5, 2),
                    "tp1_gain_pct": 50.0,
                    "stop_loss_price": best.suggested_stop_loss_price,
                    "stop_loss_loss_pct": 50.0,
                    "suggested_contracts": best.suggested_contracts,
                    "total_capital": best.total_dollar_risk,
                    "max_risk": best.stop_loss_dollar_risk,
                    "sector": sector,
                    "sector_label": sector.replace("_", " ").title(),
                    "rationale": [
                        f"Delta {best.delta:.2f} matches 0.30–0.55 delta target.",
                        f"Spread {best.spread_pct_of_mid:.1f}% of mid (${best.spread:.2f} wide).",
                        f"Liquidity: {best.open_interest:,} OI with {best.volume:,} volume.",
                        *([
                            f"Edge model: {best.trade_plan.prob_target_before_stop_pct:.0f}% chance of +50% before -50% stop, "
                            f"{best.trade_plan.expected_return_pct:+.1f}% expected on premium; options {best.vol_regime.lower()} vs realized vol."
                        ] if best.trade_plan and best.trade_plan.prob_target_before_stop_pct is not None else []),
                    ],
                    "vertical_spread": v_spread,
                    "audit_rejections": screening.audit_log,
                    **edge_fields(best),
                })
        except Exception as exc:
            logger.debug("Live options screening failed for %s: %s", sym, exc)

    if not candidates:
        # No live contract passed screening. Return nothing rather than made-up prices.
        _LIVE_OPTIONS_STATUS.update({
            "state": "empty",
            "checked_at": now,
            "symbols_screened": len(symbols_to_screen),
            "message": (
                f"No live contracts passed screening across {len(symbols_to_screen)} stocks. "
                "Market data may be unavailable or no contract met the liquidity and delta filters. Retry shortly."
            ),
        })
        _LIVE_OPTIONS_CACHE["timestamp"] = now
        _LIVE_OPTIONS_CACHE["items"] = []
        return []

    _LIVE_OPTIONS_STATUS.update({
        "state": "ok",
        "checked_at": now,
        "symbols_screened": len(symbols_to_screen),
        "message": f"{len(candidates)} live contracts screened.",
    })
    _LIVE_OPTIONS_CACHE["timestamp"] = now
    _LIVE_OPTIONS_CACHE["items"] = candidates
    return candidates


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

    # Determine directional bias and preserve actual signal strength
    bias_clean = (bias or "").strip().upper()
    momentum = None
    sentiment = None
    derived_sig = None
    hist = None

    try:
        hist = get_price_history(sym, period="3mo")
        if hist is not None and not hist.empty and len(hist) >= 10:
            momentum = analyze_momentum(hist, sym)
            try:
                news_articles = get_company_news(sym, limit=5)
                sentiment = analyze_news_sentiment(news_articles, sym)
            except Exception:
                pass
            derived_sig = generate_signal(momentum, sentiment)
    except Exception as exc:
        logger.debug("Error analyzing signal for %s: %s", sym, exc)

    if bias_clean in ("BULLISH", "BULL", "CALL"):
        direction = BiasDirection.BULLISH
    elif bias_clean in ("BEARISH", "BEAR", "PUT"):
        direction = BiasDirection.BEARISH
    elif derived_sig and derived_sig.bias in (BiasDirection.BULLISH, BiasDirection.BEARISH):
        direction = derived_sig.bias
    elif momentum and getattr(momentum, "momentum_score", 0.0) < 0:
        direction = BiasDirection.BEARISH
    else:
        direction = BiasDirection.BULLISH

    # Preserve genuine confidence from technical signal
    if derived_sig:
        if not bias_clean or (bias_clean and derived_sig.bias == direction):
            sig_conf = derived_sig.confidence
            sig_tier = derived_sig.confidence_tier
            sig_score = derived_sig.combined_score
            rationale_items = derived_sig.rationale[:4]
        else:
            # User manually forced a direction contrary or unsupported by technicals
            sig_conf = max(0.20, min(0.48, derived_sig.confidence * 0.7))
            sig_tier = ConfidenceTier.LOW
            sig_score = 0.3 if direction == BiasDirection.BULLISH else -0.3
            rationale_items = [f"User-selected bias ({direction.value}) with mixed technical momentum."]
    else:
        sig_conf = 0.35
        sig_tier = ConfidenceTier.LOW
        sig_score = 0.3 if direction == BiasDirection.BULLISH else -0.3
        rationale_items = [f"Directional bias: {direction.value} (limited technical history)."]

    signal = TradeSignal(
        symbol=sym,
        bias=direction,
        combined_score=sig_score,
        confidence=sig_conf,
        confidence_tier=sig_tier,
        momentum_score=momentum.momentum_score if momentum else 0.0,
        sentiment_score=sentiment.overall_score if sentiment else 0.0,
        is_earnings_blackout=False,
        rationale=rationale_items,
    )

    risk_cfg = RiskManagementConfig(
        account_equity=equity,
        max_risk_pct=max(risk_pct, 0.0) / 100.0,
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
        market_ctx=_edge_ctx(
            sym, stock_price, hist, signal,
            get_earnings_info(sym, DEFAULT_CONFIG.earnings.blackout_days, DEFAULT_CONFIG.earnings.warning_days),
        ),
    )
    _journal_screening(screening, sym, signal, "options-recommend")

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
            **edge_fields(s),
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
        "signal": {
            "bias": direction.value,
            "confidence_pct": round(signal.confidence * 100.0, 1),
            "confidence_tier": signal.confidence_tier.value,
            "combined_score": round(signal.combined_score, 2),
            "rationale": signal.rationale,
        },
        "has_options": True,
        "single_leg": single_leg,
        "vertical_spread": vertical_spread,
        "moonshot_setup": moonshot_setup,
        "elevated_iv": bool(screening.elevated_iv),
        "avg_iv_pct": float(screening.avg_iv_pct),
        "audit_log": screening.audit_log,
        "iv_hv_ratio": screening.iv_hv_ratio,
        "vol_regime": screening.vol_regime,
        "realized_vol_pct": screening.realized_vol_pct,
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
    # Screen live options from fetched chains or screener cache
    items = _get_live_options_recommendations()

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
    elif s in ("edge", "expected_return"):
        # Simulated payoff under the trade plan's exits; ideas without an edge estimate go last
        items.sort(key=lambda x: (x.get("edge_score") is not None, x.get("edge_score") or 0.0), reverse=True)
    elif s in ("delta",):
        items.sort(key=lambda x: abs(x["delta"]), reverse=True)
    elif s in ("price", "cost", "ask"):
        items.sort(key=lambda x: x["price"])
    elif s in ("dte", "expiration"):
        items.sort(key=lambda x: x["dte"])
    else:
        items.sort(key=lambda x: x["confidence_pct"], reverse=True)

    # Compute dynamic market regime from actual ^VIX quote
    market_regime = None
    try:
        vix_quote = get_current_quote("^VIX")
        if vix_quote and vix_quote.get("valid") and float(vix_quote.get("current_price", 0.0)) > 0:
            vix_val = round(float(vix_quote["current_price"]), 2)
            if vix_val < 15.0:
                regime_label = "Low Volatility (IV Discount)"
                regime_headline = "Subdued market volatility. Favorable premium buying environment for directional calls/puts."
            elif vix_val <= 22.0:
                regime_label = "Moderate Volatility (Balanced)"
                regime_headline = "Balanced volatility environment. Defined-risk debit spreads and momentum swings favored."
            else:
                regime_label = "Elevated Volatility (High Risk / IV Premium)"
                regime_headline = "Elevated volatility. Rich options extrinsic premiums; defined-risk spreads advised."
            market_regime = {
                "vix": vix_val,
                "regime": regime_label,
                "headline": regime_headline,
                "status": "live",
                "source": "^VIX via yfinance",
                "updated_at_utc": datetime.now(timezone.utc).isoformat(),
            }
        else:
            market_regime = {
                "vix": None,
                "regime": "Unavailable",
                "headline": "Live VIX index quote currently unavailable from data provider.",
                "status": "unavailable",
                "source": "^VIX",
                "updated_at_utc": datetime.now(timezone.utc).isoformat(),
            }
    except Exception as exc:
        logger.debug("Failed to retrieve VIX quote: %s", exc)
        market_regime = {
            "vix": None,
            "regime": "Unavailable",
            "headline": "Live VIX index quote currently unavailable from data provider.",
            "status": "unavailable",
            "source": "^VIX",
            "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        }

    return sanitize_json({
        "total": len(items),
        "live_status": {k: _LIVE_OPTIONS_STATUS[k] for k in ("state", "symbols_screened", "message")},
        "data_source": "yfinance (delayed ~15m)",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "disclaimer": "Options quotes are delayed ~15m. Win probability is a theoretical Black-Scholes estimate N(d2). Slippage and broker fees excluded.",
        "market_regime": market_regime,
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
                    "occ_symbol": sym if occ_info else None,
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
                "occ_symbol": key if parse_occ_symbol(key) else (sym if parse_occ_symbol(sym) else None),
            })

    if not extracted:
        return {"quotes": {}}

    results: Dict[str, Any] = {}
    all_syms_set = []
    for it in extracted:
        if it["asset_type"] == "OPTION":
            # Options are priced by their OCC symbol, never by the underlying ticker
            if it["occ_symbol"]:
                all_syms_set.append(it["occ_symbol"])
        elif it["symbol"]:
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
                if asset_type == "OPTION":
                    # Unpriceable option (no OCC symbol, e.g. a spread label) -> invalid quote, not the stock price
                    px, prev_close = _get_price(item["occ_symbol"]) if item["occ_symbol"] else (0.0, 0.0)
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

    quotes = await run_in_threadpool(fetch_paper_quotes, items[:60])
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
    res = await run_in_threadpool(cache.refresh_cache, force=req_force, tickers=req_tickers)
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
            raise HTTPException(status_code=404, detail=f"No price data available for {target_symbol}")

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
