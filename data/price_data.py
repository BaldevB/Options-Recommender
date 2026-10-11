"""Price data fetching, quote normalization, caching, and earnings calendar checks using yfinance."""

from datetime import datetime, date, timedelta, timezone
import logging
import time
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd
import yfinance as yf
from config import DEFAULT_CONFIG, INDEX_PRODUCTS

logger = logging.getLogger(__name__)

# Simple in-memory cache for market data: {cache_key: (timestamp, data)}
_CACHE: Dict[str, Any] = {}
CACHE_TTL = DEFAULT_CONFIG.cache_ttl_seconds

# Default periods for each timeframe interval
DEFAULT_TIMEFRAME_PERIODS: Dict[str, str] = {
    "1m": "1d",
    "2m": "1d",
    "5m": "5d",
    "15m": "5d",
    "30m": "1mo",
    "60m": "1mo",
    "1h": "1mo",
    "1d": "6mo",
    "1wk": "1y",
    "1mo": "2y",
}


def _get_from_cache(key: str) -> Optional[Any]:
    if key in _CACHE:
        ts, val = _CACHE[key]
        if time.time() - ts < CACHE_TTL:
            return val
        del _CACHE[key]
    return None


def _set_in_cache(key: str, val: Any) -> None:
    _CACHE[key] = (time.time(), val)


def normalize_timeframe(interval: str = "1d", period: Optional[str] = None) -> Tuple[str, str]:
    """Ensure interval and period are compatible with yfinance limitations."""
    itv = (interval or "1d").strip().lower()
    per = (period or "").strip().lower()

    if not per:
        per = DEFAULT_TIMEFRAME_PERIODS.get(itv, "6mo")

    # yfinance period limits for intraday intervals
    if itv in ["1m", "2m"]:
        if per not in ["1d", "5d", "7d"]:
            per = "1d"
    elif itv in ["5m", "15m", "30m"]:
        if per in ["3mo", "6mo", "1y", "2y", "5y", "max"]:
            per = "5d"
    elif itv in ["60m", "1h"]:
        if per in ["1y", "2y", "5y", "max"]:
            per = "1mo"

    return itv, per


def get_price_history(symbol: str, period: str = "6mo", interval: str = "1d") -> Optional[pd.DataFrame]:
    """Fetch OHLCV historical dataframe for a symbol with in-memory caching and interval support.

    Args:
        symbol: Ticker symbol (e.g. 'AAPL')
        period: Period string (e.g. '1d', '5d', '1mo', '6mo', '1y')
        interval: Bar interval (e.g. '1m', '5m', '15m', '1h', '1d', '1wk')

    Returns:
        pd.DataFrame with DatetimeIndex and columns ['Open', 'High', 'Low', 'Close', 'Volume']
        or None if failed.
    """
    symbol = symbol.strip().upper()
    interval, period = normalize_timeframe(interval, period)
    cache_key = f"hist_{symbol}_{period}_{interval}"
    cached = _get_from_cache(cache_key)
    if cached is not None:
        return cached.copy()

    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval, auto_adjust=True)

        if df is None or df.empty:
            logger.warning("No price history returned for symbol %s (interval=%s, period=%s)", symbol, interval, period)
            return None

        # Flatten multi-level columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        required_cols = ["Open", "High", "Low", "Close", "Volume"]
        for col in required_cols:
            if col not in df.columns:
                logger.error("Missing expected column %s for %s", col, symbol)
                return None

        df = df[required_cols].copy()
        df.dropna(subset=["Close"], inplace=True)
        # Drop duplicate timestamps if any
        df = df[~df.index.duplicated(keep="first")]
        df.sort_index(inplace=True)

        _set_in_cache(cache_key, df)
        return df.copy()

    except Exception as exc:
        logger.error("Error fetching price history for %s: %s", symbol, exc)
        return None


def get_candles_data(
    symbol: str,
    interval: str = "1d",
    period: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Fetch OHLCV candles formatted for TradingView Lightweight Charts with indicators and VWAP.

    Args:
        symbol: Ticker symbol (e.g. 'NVDA')
        interval: Candle timeframe ('1m', '5m', '15m', '1h', '1d', '1wk')
        period: Optional historical lookback ('1d', '5d', '1mo', '6mo', '1y')

    Returns:
        List of dicts with: time, open, high, low, close, volume, sma20, sma50, vwap.
    """
    symbol = symbol.strip().upper()
    interval, period = normalize_timeframe(interval, period)

    cache_key = f"candles_{symbol}_{period}_{interval}"
    cached = _get_from_cache(cache_key)
    if cached is not None:
        return cached

    df = get_price_history(symbol, period=period, interval=interval)
    if df is None or df.empty:
        return []

    df = df.copy()
    # Moving Averages
    df["SMA20"] = df["Close"].rolling(window=min(20, len(df))).mean()
    df["SMA50"] = df["Close"].rolling(window=min(50, len(df))).mean()

    # VWAP for intraday
    is_intraday = interval in ["1m", "2m", "5m", "15m", "30m", "60m", "1h"]
    if is_intraday:
        typ = (df["High"] + df["Low"] + df["Close"]) / 3.0
        cum_pv = (typ * df["Volume"]).cumsum()
        cum_vol = df["Volume"].cumsum()
        df["VWAP"] = cum_pv / cum_vol.replace(0, np.nan)
    else:
        df["VWAP"] = np.nan

    candles: List[Dict[str, Any]] = []
    for dt, row in df.iterrows():
        # UNIX timestamp (seconds) for intraday, YYYY-MM-DD string for daily/weekly
        if is_intraday:
            t = int(dt.timestamp())
        else:
            t = dt.strftime("%Y-%m-%d") if hasattr(dt, "strftime") else str(dt)[:10]

        candles.append({
            "time": t,
            "open": round(float(row["Open"]), 2),
            "high": round(float(row["High"]), 2),
            "low": round(float(row["Low"]), 2),
            "close": round(float(row["Close"]), 2),
            "volume": int(row["Volume"]),
            "sma20": round(float(row["SMA20"]), 2) if not pd.isna(row["SMA20"]) else None,
            "sma50": round(float(row["SMA50"]), 2) if not pd.isna(row["SMA50"]) else None,
            "vwap": round(float(row["VWAP"]), 2) if not pd.isna(row["VWAP"]) else None,
        })

    _set_in_cache(cache_key, candles)
    return candles


def get_current_quote(symbol: str) -> Dict[str, Any]:
    """Fetch latest quote and basic metadata for a symbol with caching.

    Returns:
        Dictionary containing current_price, prev_close, change, change_percent,
        day_high, day_low, 52w_high, 52w_low, volume, name, valid.
    """
    symbol = symbol.strip().upper()
    cache_key = f"quote_{symbol}"
    cached = _get_from_cache(cache_key)
    if cached is not None:
        return cached.copy()

    quote: Dict[str, Any] = {
        "symbol": symbol,
        "name": symbol,
        "current_price": 0.0,
        "previous_close": 0.0,
        "change": 0.0,
        "change_percent": 0.0,
        "day_high": 0.0,
        "day_low": 0.0,
        "fifty_two_week_high": 0.0,
        "fifty_two_week_low": 0.0,
        "volume": 0,
        "valid": False,
    }

    try:
        ticker = yf.Ticker(symbol)
        fast_info = getattr(ticker, "fast_info", None)

        if fast_info:
            price = getattr(fast_info, "last_price", None) or getattr(fast_info, "regular_market_price", None)
            prev_close = getattr(fast_info, "previous_close", None)
            day_high = getattr(fast_info, "day_high", None)
            day_low = getattr(fast_info, "day_low", None)
            year_high = getattr(fast_info, "year_high", None)
            year_low = getattr(fast_info, "year_low", None)
            volume = getattr(fast_info, "last_volume", None)

            if price is not None and not pd.isna(price):
                quote["current_price"] = float(price)
            if prev_close is not None and not pd.isna(prev_close):
                quote["previous_close"] = float(prev_close)
            if day_high is not None and not pd.isna(day_high):
                quote["day_high"] = float(day_high)
            if day_low is not None and not pd.isna(day_low):
                quote["day_low"] = float(day_low)
            if year_high is not None and not pd.isna(year_high):
                quote["fifty_two_week_high"] = float(year_high)
            if year_low is not None and not pd.isna(year_low):
                quote["fifty_two_week_low"] = float(year_low)
            if volume is not None and not pd.isna(volume):
                quote["volume"] = int(volume)

        # Fallback to recent history if fast_info missing
        if quote["current_price"] <= 0.0:
            hist = ticker.history(period="5d")
            if hist is not None and not hist.empty:
                quote["current_price"] = float(hist["Close"].iloc[-1])
                if len(hist) > 1:
                    quote["previous_close"] = float(hist["Close"].iloc[-2])
                quote["day_high"] = float(hist["High"].iloc[-1])
                quote["day_low"] = float(hist["Low"].iloc[-1])
                quote["volume"] = int(hist["Volume"].iloc[-1])

        try:
            info = getattr(ticker, "info", {})
            if isinstance(info, dict):
                quote["name"] = info.get("shortName") or info.get("longName") or symbol
        except Exception:
            pass

        if quote["current_price"] > 0:
            quote["valid"] = True
            if quote["previous_close"] > 0:
                quote["change"] = round(quote["current_price"] - quote["previous_close"], 2)
                quote["change_percent"] = round((quote["change"] / quote["previous_close"]) * 100, 2)

        _set_in_cache(cache_key, quote)

    except Exception as exc:
        logger.error("Error fetching current quote for %s: %s", symbol, exc)

    return quote


def get_earnings_info(
    symbol: str,
    blackout_days: int = 10,
    warning_days: int = 21
) -> Dict[str, Any]:
    """Retrieve upcoming earnings date and determine if within blackout window.

    Args:
        symbol: Ticker symbol
        blackout_days: Days threshold to trigger earnings blackout
        warning_days: Days threshold to trigger warning

    Returns:
        Dict: {
            'next_earnings_date': str or None,
            'days_to_earnings': int or None,
            'is_blackout': bool,
            'is_warning': bool,
            'status_message': str
        }
    """
    symbol = symbol.strip().upper()
    cache_key = f"earnings_{symbol}"
    cached = _get_from_cache(cache_key)
    if cached is not None:
        return cached.copy()

    result: Dict[str, Any] = {
        "next_earnings_date": None,
        "days_to_earnings": None,
        "is_blackout": False,
        "is_warning": False,
        "status_message": "No imminent earnings detected.",
    }

    try:
        ticker = yf.Ticker(symbol)
        today = date.today()
        upcoming_dates = []

        # Check calendar
        cal = getattr(ticker, "calendar", None)
        if isinstance(cal, dict) and "Earnings Date" in cal:
            e_dates = cal["Earnings Date"]
            if isinstance(e_dates, list):
                for ed in e_dates:
                    if isinstance(ed, (date, datetime)):
                        d = ed.date() if isinstance(ed, datetime) else ed
                        if d >= today:
                            upcoming_dates.append(d)

        # Check earnings_dates if calendar was empty
        if not upcoming_dates:
            ed_df = getattr(ticker, "earnings_dates", None)
            if ed_df is not None and not ed_df.empty:
                for idx_dt in ed_df.index:
                    try:
                        d = idx_dt.date() if hasattr(idx_dt, "date") else idx_dt
                        if d >= today:
                            upcoming_dates.append(d)
                    except Exception:
                        pass

        if upcoming_dates:
            upcoming_dates.sort()
            next_date = upcoming_dates[0]
            days_away = (next_date - today).days

            result["next_earnings_date"] = next_date.strftime("%Y-%m-%d")
            result["days_to_earnings"] = days_away

            if days_away <= blackout_days:
                result["is_blackout"] = True
                result["is_warning"] = True
                result["status_message"] = (
                    f"[EARNINGS BLACKOUT] Earnings expected in {days_away} day(s) ({result['next_earnings_date']}). "
                    f"Directional options carry severe binary gap and IV crush risk."
                )
            elif days_away <= warning_days:
                result["is_warning"] = True
                result["status_message"] = (
                    f"[EARNINGS APPROACHING] Earnings in {days_away} days ({result['next_earnings_date']}). "
                    f"Monitor contract expiration relative to earnings."
                )
            else:
                result["status_message"] = f"Next earnings in {days_away} days ({result['next_earnings_date']})."

        _set_in_cache(cache_key, result)

    except Exception as exc:
        logger.warning("Could not retrieve earnings calendar for %s: %s", symbol, exc)

    return result


def get_dividend_info(
    symbol: str,
    blackout_days: int = 3,
    warning_days: int = 7
) -> Dict[str, Any]:
    """Retrieve upcoming ex-dividend date to protect against early assignment and price drop.

    Returns:
        Dict with 'next_ex_dividend_date', 'days_to_dividend', 'is_dividend_risk', 'status_message'.
    """
    symbol = symbol.strip().upper()
    cache_key = f"dividend_{symbol}"
    cached = _get_from_cache(cache_key)
    if cached is not None:
        return cached.copy()

    result: Dict[str, Any] = {
        "next_ex_dividend_date": None,
        "days_to_dividend": None,
        "is_dividend_risk": False,
        "status_message": "No imminent ex-dividend date detected.",
    }

    try:
        ticker = yf.Ticker(symbol)
        today = date.today()
        upcoming = []

        # Check calendar for Ex-Dividend Date
        cal = getattr(ticker, "calendar", None)
        if isinstance(cal, dict) and "Ex-Dividend Date" in cal:
            ex_val = cal["Ex-Dividend Date"]
            if isinstance(ex_val, (date, datetime)):
                d = ex_val.date() if isinstance(ex_val, datetime) else ex_val
                if d >= today:
                    upcoming.append(d)

        # Check fast_info or info
        if not upcoming:
            info = getattr(ticker, "info", {})
            if isinstance(info, dict) and "exDividendDate" in info:
                ts = info["exDividendDate"]
                if ts and isinstance(ts, (int, float)):
                    d = datetime.fromtimestamp(ts, tz=timezone.utc).date()
                    if d >= today:
                        upcoming.append(d)

        if upcoming:
            upcoming.sort()
            next_div = upcoming[0]
            days_away = (next_div - today).days
            result["next_ex_dividend_date"] = next_div.strftime("%Y-%m-%d")
            result["days_to_dividend"] = days_away

            if days_away <= blackout_days:
                result["is_dividend_risk"] = True
                result["status_message"] = (
                    f"[EX-DIVIDEND WARNING] Ex-dividend date in {days_away} day(s) ({result['next_ex_dividend_date']}). "
                    f"Short call early assignment risk and underlying dividend gap down risk."
                )
            elif days_away <= warning_days:
                result["status_message"] = (
                    f"Ex-dividend date approaching in {days_away} days ({result['next_ex_dividend_date']})."
                )

        _set_in_cache(cache_key, result)
    except Exception as exc:
        logger.debug("Could not retrieve dividend info for %s: %s", symbol, exc)

    return result


def get_macro_event_info(symbol: str) -> Dict[str, Any]:
    """Check macro event schedule (FOMC rate decision, CPI release) for broad index products.

    Index ETFs (SPY, QQQ, IWM, DIA) are strongly impacted by binary macro announcements.
    """
    symbol = symbol.strip().upper()
    is_index = symbol in INDEX_PRODUCTS

    today = date.today()

    # Recurring macro calendar dates (FOMC announcements & CPI releases)
    # Modeled schedule for 2026/2027 macroeconomic calendar
    macro_schedule = [
        # Modeled upcoming FOMC/CPI dates for current/upcoming cycles
        {"event": "CPI Release (Inflation Print)", "date": date(2026, 10, 14), "type": "CPI"},
        {"event": "FOMC Rate Decision", "date": date(2026, 11, 4), "type": "FOMC"},
        {"event": "CPI Release (Inflation Print)", "date": date(2026, 11, 12), "type": "CPI"},
        {"event": "FOMC Rate Decision", "date": date(2026, 12, 16), "type": "FOMC"},
        {"event": "CPI Release (Inflation Print)", "date": date(2026, 12, 11), "type": "CPI"},
        {"event": "FOMC Rate Decision", "date": date(2027, 1, 27), "type": "FOMC"},
    ]

    upcoming_macro = [m for m in macro_schedule if m["date"] >= today]
    upcoming_macro.sort(key=lambda x: x["date"])

    if not is_index or not upcoming_macro:
        return {
            "is_index_product": is_index,
            "next_macro_event": None,
            "days_to_macro_event": None,
            "is_macro_risk": False,
            "status_message": "Single equity product (specific idiosyncratic earnings/sentiment applies)."
        }

    next_ev = upcoming_macro[0]
    days_to_macro = (next_ev["date"] - today).days

    is_risk = (days_to_macro <= 2)

    return {
        "is_index_product": True,
        "next_macro_event": next_ev["event"],
        "macro_date": next_ev["date"].strftime("%Y-%m-%d"),
        "days_to_macro_event": days_to_macro,
        "is_macro_risk": is_risk,
        "status_message": (
            f"[MACRO EVENT ALERT] {next_ev['event']} in {days_to_macro} day(s) ({next_ev['date'].strftime('%Y-%m-%d')}). "
            f"Elevated implied volatility and binary market gap risk across index products."
            if is_risk else
            f"Next key macro event: {next_ev['event']} in {days_to_macro} days."
        )
    }


def get_event_risk_profile(symbol: str) -> Dict[str, Any]:
    """Synthesize complete institutional event risk profile (Earnings, Dividends, Macro)."""
    earnings = get_earnings_info(symbol)
    dividends = get_dividend_info(symbol)
    macro = get_macro_event_info(symbol)

    has_event_soon = (
        earnings.get("is_blackout", False) or
        earnings.get("is_warning", False) or
        dividends.get("is_dividend_risk", False) or
        macro.get("is_macro_risk", False)
    )

    reasons = []
    if earnings.get("is_blackout"):
        reasons.append(f"Earnings Blackout ({earnings.get('days_to_earnings')}d)")
    elif earnings.get("is_warning"):
        reasons.append(f"Earnings Approaching ({earnings.get('days_to_earnings')}d)")

    if dividends.get("is_dividend_risk"):
        reasons.append(f"Ex-Dividend ({dividends.get('days_to_dividend')}d)")

    if macro.get("is_macro_risk"):
        reasons.append(f"Macro {macro.get('next_macro_event')} ({macro.get('days_to_macro_event')}d)")

    return {
        "symbol": symbol,
        "has_event_soon": has_event_soon,
        "reasons": reasons,
        "earnings": earnings,
        "dividends": dividends,
        "macro": macro,
        "recommend_spread_over_single_leg": has_event_soon,
        "is_index_product": macro.get("is_index_product", False),
        "has_macro_event": macro.get("next_macro_event") is not None,
        "macro_event_name": macro.get("next_macro_event") or "None",
        "has_dividend_event": dividends.get("next_ex_dividend_date") is not None,
        "event_warnings": reasons,
    }


RIBBON_BENCHMARKS: List[Dict[str, str]] = [
    {"symbol": "SPY", "name": "S&P 500"},
    {"symbol": "QQQ", "name": "Nasdaq 100"},
    {"symbol": "IWM", "name": "Russell 2000"},
    {"symbol": "DIA", "name": "Dow Jones"},
    {"symbol": "^VIX", "name": "VIX Volatility"},
    {"symbol": "BTC-USD", "name": "Bitcoin"},
    {"symbol": "GLD", "name": "Gold"},
    {"symbol": "USO", "name": "Crude Oil"},
]


def get_market_session_status() -> Dict[str, Any]:
    """Determine US stock market trading session status in Eastern Time (America/New_York)."""
    try:
        import zoneinfo
        now_et = datetime.now(zoneinfo.ZoneInfo("America/New_York"))
    except Exception:
        now_et = datetime.now(timezone(timedelta(hours=-4)))

    weekday = now_et.weekday()  # 0 = Mon, 6 = Sun
    time_min = now_et.hour * 60 + now_et.minute

    if weekday in (5, 6):
        return {
            "status": "CLOSED",
            "label": "Market Closed (Weekend)",
            "et_time": now_et.strftime("%I:%M %p ET"),
            "is_open": False,
        }

    # Mon-Fri schedule
    if 570 <= time_min < 960:  # 9:30 AM to 4:00 PM
        return {
            "status": "REGULAR",
            "label": "Regular Session Open",
            "et_time": now_et.strftime("%I:%M %p ET"),
            "is_open": True,
        }
    elif 240 <= time_min < 570:  # 4:00 AM to 9:30 AM
        return {
            "status": "PRE_MARKET",
            "label": "Pre-Market Session",
            "et_time": now_et.strftime("%I:%M %p ET"),
            "is_open": False,
        }
    elif 960 <= time_min < 1200:  # 4:00 PM to 8:00 PM
        return {
            "status": "AFTER_HOURS",
            "label": "After-Hours Session",
            "et_time": now_et.strftime("%I:%M %p ET"),
            "is_open": False,
        }
    else:
        return {
            "status": "CLOSED",
            "label": "Market Closed (Overnight)",
            "et_time": now_et.strftime("%I:%M %p ET"),
            "is_open": False,
        }


def get_market_ribbon_data() -> Dict[str, Any]:
    """Retrieve fast cached quotes for key market indices and commodities ribbon."""
    cache_key = "market_ribbon_bundle"
    cached = _get_from_cache(cache_key)
    session = get_market_session_status()

    if cached is not None:
        cached_copy = cached.copy()
        cached_copy["session"] = session
        return cached_copy

    items: List[Dict[str, Any]] = []
    for b in RIBBON_BENCHMARKS:
        sym = b["symbol"]
        q = get_current_quote(sym)
        items.append({
            "symbol": sym,
            "name": b["name"],
            "price": q.get("current_price", 0.0),
            "previous_close": q.get("previous_close", 0.0),
            "change": q.get("change", 0.0),
            "change_percent": q.get("change_percent", 0.0),
            "day_high": q.get("day_high", 0.0),
            "day_low": q.get("day_low", 0.0),
            "valid": q.get("valid", False),
        })

    result = {
        "session": session,
        "benchmarks": items,
        "updated_at": datetime.now().isoformat(),
    }
    _set_in_cache(cache_key, result)
    return result


def get_watchlist_summary(symbols: List[str]) -> List[Dict[str, Any]]:
    """Retrieve batch quote and momentum summary for user's starred watchlist."""
    results: List[Dict[str, Any]] = []
    clean_syms = list(dict.fromkeys([s.strip().upper() for s in symbols if s and s.strip()]))

    for sym in clean_syms:
        try:
            q = get_current_quote(sym)
            if not q.get("valid") and q.get("current_price", 0.0) <= 0:
                continue

            hist = get_price_history(sym, period="6mo")
            mom_data = None
            if hist is not None and not hist.empty:
                try:
                    from analysis.momentum import analyze_momentum
                    from config import TechnicalConfig
                    mom = analyze_momentum(hist, sym, TechnicalConfig())
                    mom_data = {
                        "score": round(mom.momentum_score, 1),
                        "rsi": round(mom.rsi, 1),
                        "trend": mom.trend_description,
                        "volume_ratio": round(mom.volume_ratio, 2),
                        "volume_confirmed": mom.volume_confirmed,
                        "weekly_trend": mom.weekly_trend,
                    }
                except Exception:
                    pass

            results.append({
                "symbol": sym,
                "name": q.get("name", sym),
                "price": q.get("current_price", 0.0),
                "previous_close": q.get("previous_close", 0.0),
                "change": q.get("change", 0.0),
                "change_percent": q.get("change_percent", 0.0),
                "day_high": q.get("day_high", 0.0),
                "day_low": q.get("day_low", 0.0),
                "volume": q.get("volume", 0),
                "momentum": mom_data,
            })
        except Exception as exc:
            logger.warning("Error fetching watchlist summary for %s: %s", sym, exc)

    return results
