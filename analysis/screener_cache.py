"""High-speed in-memory Screener Cache & Intraday Background Refresh Manager.

Maintains thread-safe pre-computed stock recommendations across 1,000+ US equities,
supporting sub-second multi-parameter filtering (horizon, sector, search), multi-column
sorting, pagination, on-demand deep-dive analysis, and background batch refreshes.
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
    }


def fetch_single_stock_analysis(symbol: str) -> Optional[Dict[str, Any]]:
    """Fetch on-demand deep dive stock analysis for any US equity symbol."""
    try:
        from data.price_data import get_current_quote, get_price_history, get_earnings_info
        from analysis.sentiment import analyze_sentiment

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
            sentiment = analyze_sentiment(symbol)
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

    def __init__(self) -> None:
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
        search: Optional[str] = None,
        sort_by: str = "score",
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Query, filter, sort, and paginate cached stock recommendations in sub-second time.

        Args:
            horizon: Filter by timeframe horizon ('ALL', 'SWING', 'LONG_TERM', 'BREAKOUT').
            sector: Filter by sector slug or human-readable name.
            search: Ticker symbol or company name search substring.
            sort_by: Sorting field ('score', 'symbol', 'price', 'change_pct', 'volume_ratio', 'rsi', etc.).
            limit: Page size limit (default 50).
            offset: Page offset (default 0).

        Returns:
            Dict containing total count, page items, pagination metadata, and updated timestamp.
        """
        with self._lock:
            items_snapshot = list(self._cached_items)
            updated_at = self._last_updated

        filtered: List[Dict[str, Any]] = []

        # Parse horizon filter
        h_norm = horizon.strip().upper() if horizon else None
        if h_norm in ("ALL", "", "NONE"):
            h_norm = None

        # Parse sector filter
        s_norm = normalize_sector_query(sector)

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

            # 3. Search query
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
        """Retrieve full deep dive analysis for a symbol from cache or on-demand scan.

        Args:
            symbol: Ticker symbol (e.g. 'NVDA')

        Returns:
            Dictionary with trade plan, scoring, and indicators, or None if unavailable.
        """
        sym = symbol.strip().upper()
        with self._lock:
            if sym in self._cached_dict:
                return dict(self._cached_dict[sym])

        # On-demand fallback
        analysis = fetch_single_stock_analysis(sym)
        if analysis:
            with self._lock:
                self._cached_dict[sym] = analysis
            return dict(analysis)

        return None

    def get_status(self) -> Dict[str, Any]:
        """Return cache health, stock counts, refresh timestamps, and worker status."""
        with self._lock:
            return {
                "status": self._status,
                "last_updated": self._last_updated,
                "cached_stocks": len(self._cached_items),
                "total_stocks": len(get_stock_universe()),
                "is_refreshing": self._is_refreshing,
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

        Args:
            force: Force refresh even if a refresh is currently marked active.
            tickers: Optional list of tickers to scan (defaults to entire stock universe).
            chunk_size: Number of tickers per batch yfinance request.

        Returns:
            Status summary dictionary.
        """
        with self._lock:
            if self._is_refreshing and not force:
                return {
                    "status": "already_refreshing",
                    "updated_at": self._last_updated,
                    "cached_stocks": len(self._cached_items),
                }
            self._is_refreshing = True
            self._status = "refreshing"

        try:
            if tickers is None:
                universe_items = get_stock_universe()
                all_tickers = [item["symbol"] for item in universe_items]
            else:
                all_tickers = [t.strip().upper() for t in tickers if t and t.strip()]

            # Deduplicate tickers while maintaining order
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
                        recs.append(rec_dict)
                    except Exception as sym_exc:
                        logger.debug("Skipping symbol %s due to computation error: %s", sym, sym_exc)
                        continue

            if recs:
                self._set_cached_items(recs)
                logger.info("Stock screener cache refreshed successfully with %d stocks.", len(recs))
                return {
                    "status": "success",
                    "scanned_stocks": len(recs),
                    "updated_at": self._last_updated,
                }
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
            for _ in range(sleep_secs):
                if self._stop_worker_event.is_set():
                    break
                time.sleep(1.0)


_GLOBAL_SCREENER_CACHE: Optional[StockScreenerCache] = None
_GLOBAL_CACHE_LOCK = threading.Lock()


def get_screener_cache() -> StockScreenerCache:
    """Retrieve or initialize the global thread-safe StockScreenerCache singleton."""
    global _GLOBAL_SCREENER_CACHE
    if _GLOBAL_SCREENER_CACHE is None:
        with _GLOBAL_CACHE_LOCK:
            if _GLOBAL_SCREENER_CACHE is None:
                _GLOBAL_SCREENER_CACHE = StockScreenerCache()
    return _GLOBAL_SCREENER_CACHE
