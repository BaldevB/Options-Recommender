"""Options chain retrieval and expiration filtering using yfinance."""

from datetime import datetime, date, timezone
import logging
import time
from typing import List, Tuple, Dict, Any, Optional
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

# Bounded in-memory cache for full option chain matrices: {cache_key: (timestamp, data)}
_MATRIX_CACHE: Dict[str, Tuple[float, Any]] = {}
MATRIX_CACHE_TTL = 300.0  # 5 minutes TTL
MAX_MATRIX_CACHE_ENTRIES = 25


def _prune_expired_matrix_cache() -> None:
    """Evict expired options matrices to prevent memory buildup on cloud containers."""
    now = time.time()
    expired = [k for k, (ts, _) in _MATRIX_CACHE.items() if (now - ts) > MATRIX_CACHE_TTL]
    for k in expired:
        _MATRIX_CACHE.pop(k, None)


def _store_in_matrix_cache(key: str, data: Any) -> None:
    _prune_expired_matrix_cache()
    if len(_MATRIX_CACHE) >= MAX_MATRIX_CACHE_ENTRIES:
        oldest = min(_MATRIX_CACHE.keys(), key=lambda k: _MATRIX_CACHE[k][0])
        _MATRIX_CACHE.pop(oldest, None)
    _MATRIX_CACHE[key] = (time.time(), data)


def get_available_expirations(symbol: str) -> List[str]:
    """Retrieve list of expiration date strings (YYYY-MM-DD) for a symbol with retry."""
    sym = symbol.strip().upper().replace(".", "-")
    for attempt in range(2):
        try:
            ticker = yf.Ticker(sym)
            options = ticker.options
            if options:
                return list(options)
            time.sleep(0.3)
        except Exception as exc:
            logger.warning("Attempt %d: Failed to fetch expirations for %s: %s", attempt + 1, sym, exc)
            time.sleep(0.3)
    return []


def calculate_dte(expiration_str: str) -> int:
    """Calculate Days To Expiration (DTE) from an expiration date string."""
    try:
        exp_date = datetime.strptime(expiration_str, "%Y-%m-%d").date()
        today = date.today()
        return (exp_date - today).days
    except Exception:
        return -1


def filter_expirations_by_dte(
    expirations: List[str],
    min_dte: int = 14,
    max_dte: int = 45
) -> List[Tuple[str, int]]:
    """Filter expiration dates that fall within the [min_dte, max_dte] window.

    Supports 0DTE (min_dte=0) for same-day expirations.

    Returns:
        List of tuples: [(expiration_date, dte), ...]
    """
    valid_exps: List[Tuple[str, int]] = []
    all_with_dte: List[Tuple[str, int]] = []

    for exp in expirations:
        dte = calculate_dte(exp)
        if dte >= 0:
            all_with_dte.append((exp, dte))
            if min_dte <= dte <= max_dte:
                valid_exps.append((exp, dte))

    # Strict DTE filtering: return only expirations within requested window
    return valid_exps


def _clean_chain_df(df: pd.DataFrame, expiration: str, dte: int, option_type: str) -> pd.DataFrame:
    """Clean and enrich raw yfinance options dataframe."""
    if df is None or df.empty:
        return pd.DataFrame()

    clean = df.copy()

    # Fill missing values
    for num_col in ["bid", "ask", "lastPrice", "volume", "openInterest", "impliedVolatility"]:
        if num_col in clean.columns:
            clean[num_col] = pd.to_numeric(clean[num_col], errors="coerce").fillna(0.0)
        else:
            clean[num_col] = 0.0

    clean["strike"] = pd.to_numeric(clean["strike"], errors="coerce")
    clean.dropna(subset=["strike"], inplace=True)

    clean["expiration"] = expiration
    clean["dte"] = dte
    clean["type"] = option_type.upper()

    # Do not fabricate bid or ask from lastPrice. Keep lastPrice separate.
    # Calculate spread and spread ratio
    clean["spread"] = (clean["ask"] - clean["bid"]).clip(lower=0.0)
    clean["spread_ratio"] = clean.apply(
        lambda r: (r["spread"] / r["ask"]) if r["ask"] > 0 else 1.0, axis=1
    )

    # Standardize column selection
    cols = [
        "contractSymbol", "expiration", "dte", "type", "strike",
        "lastPrice", "bid", "ask", "spread", "spread_ratio",
        "volume", "openInterest", "impliedVolatility", "inTheMoney"
    ]
    existing_cols = [c for c in cols if c in clean.columns]
    return clean[existing_cols]


def get_options_chains(
    symbol: str,
    min_dte: int = 14,
    max_dte: int = 45
) -> Tuple[pd.DataFrame, pd.DataFrame, List[Tuple[str, int]]]:
    """Retrieve filtered Calls and Puts across target DTE expirations.

    Args:
        symbol: Ticker symbol
        min_dte: Minimum days to expiration
        max_dte: Maximum days to expiration

    Returns:
        Tuple: (calls_df, puts_df, filtered_expirations)
    """
    symbol = symbol.strip().upper().replace(".", "-")
    all_expirations = get_available_expirations(symbol)
    if not all_expirations:
        return pd.DataFrame(), pd.DataFrame(), []

    target_expirations = filter_expirations_by_dte(all_expirations, min_dte, max_dte)
    if not target_expirations:
        return pd.DataFrame(), pd.DataFrame(), []

    calls_list: List[pd.DataFrame] = []
    puts_list: List[pd.DataFrame] = []
    ticker = yf.Ticker(symbol)

    for exp, dte in target_expirations:
        try:
            chain = ticker.option_chain(exp)
            if chain.calls is not None and not chain.calls.empty:
                calls_list.append(_clean_chain_df(chain.calls, exp, dte, "CALL"))
            if chain.puts is not None and not chain.puts.empty:
                puts_list.append(_clean_chain_df(chain.puts, exp, dte, "PUT"))
        except Exception as exc:
            logger.warning("Error fetching option chain for %s on %s: %s", symbol, exp, exc)

    calls_df = pd.concat(calls_list, ignore_index=True) if calls_list else pd.DataFrame()
    puts_df = pd.concat(puts_list, ignore_index=True) if puts_list else pd.DataFrame()

    return calls_df, puts_df, target_expirations


def get_options_chain_matrix(
    symbol: str,
    expiration: Optional[str] = None
) -> Dict[str, Any]:
    """Retrieve full options chain matrix for a given expiration with Greeks, Max Pain, and Expected Move.

    Args:
        symbol: Ticker symbol
        expiration: Specific expiration date (YYYY-MM-DD) or None for default closest

    Returns:
        Dictionary containing chain analytics and unified strike ladder matrix
    """
    from data.price_data import get_current_quote
    from options.suggester import calculate_chain_analytics, build_chain_matrix

    symbol = symbol.strip().upper().replace(".", "-")
    quote = get_current_quote(symbol)
    spot_price = float(quote.get("current_price", 0.0))

    # Fallback to direct ticker probe if spot_price <= 0
    if spot_price <= 0:
        try:
            t = yf.Ticker(symbol)
            fi = getattr(t, "fast_info", None)
            if fi:
                p = getattr(fi, "last_price", None) or getattr(fi, "regular_market_price", None)
                if p is not None and not pd.isna(p):
                    spot_price = float(p)
            if spot_price <= 0:
                h = t.history(period="5d")
                if h is not None and not h.empty:
                    spot_price = float(h["Close"].iloc[-1])
        except Exception as exc:
            logger.warning("Could not probe spot price fallback for %s: %s", symbol, exc)

    all_expirations = get_available_expirations(symbol)
    if not all_expirations:
        return {
            "symbol": symbol,
            "name": quote.get("name", symbol),
            "current_price": spot_price,
            "change": quote.get("change", 0.0),
            "change_pct": quote.get("change_percent", 0.0),
            "available_expirations": [],
            "selected_expiration": None,
            "dte": 0,
            "analytics": {},
            "strikes": [],
            "error": f"No options available for {symbol}",
            "data_source": "yfinance (15m delayed standard equity / options quotes)",
            "retrieved_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        }

    # Build available expirations list with DTE
    exp_list = []
    for exp in all_expirations:
        d = calculate_dte(exp)
        if d >= 0:
            exp_list.append({"expiration": exp, "dte": d})

    # Select expiration: match user requested expiration, or default to closest front expiration
    target_exp = expiration
    if not target_exp or target_exp not in all_expirations:
        candidates = [e for e in exp_list if e["dte"] >= 0]
        target_exp = candidates[0]["expiration"] if candidates else exp_list[0]["expiration"]

    dte = calculate_dte(target_exp)

    cache_key = f"{symbol}_{target_exp}"
    if cache_key in _MATRIX_CACHE:
        ts, cached_data = _MATRIX_CACHE[cache_key]
        if time.time() - ts < MATRIX_CACHE_TTL:
            return cached_data

    try:
        ticker = yf.Ticker(symbol)
        chain = ticker.option_chain(target_exp)
        calls_df = _clean_chain_df(chain.calls, target_exp, dte, "CALL")
        puts_df = _clean_chain_df(chain.puts, target_exp, dte, "PUT")

        # Fallback if selected expiration returned empty chain (e.g. after-hours rollover)
        if (calls_df.empty and puts_df.empty) and len(exp_list) > 1:
            for alt_exp in [e["expiration"] for e in exp_list if e["expiration"] != target_exp][:2]:
                try:
                    alt_chain = ticker.option_chain(alt_exp)
                    alt_dte = calculate_dte(alt_exp)
                    c_alt = _clean_chain_df(alt_chain.calls, alt_exp, alt_dte, "CALL")
                    p_alt = _clean_chain_df(alt_chain.puts, alt_exp, alt_dte, "PUT")
                    if not c_alt.empty or not p_alt.empty:
                        target_exp = alt_exp
                        dte = alt_dte
                        calls_df = c_alt
                        puts_df = p_alt
                        break
                except Exception:
                    continue

        # If spot price is still 0 but we have contracts, infer spot price from strike median
        if spot_price <= 0:
            strikes = []
            if not calls_df.empty:
                strikes.extend(calls_df["strike"].tolist())
            if not puts_df.empty:
                strikes.extend(puts_df["strike"].tolist())
            if strikes:
                spot_price = float(pd.Series(strikes).median())

        if calls_df.empty and puts_df.empty:
            return {
                "symbol": symbol,
                "name": quote.get("name", symbol),
                "current_price": spot_price,
                "change": quote.get("change", 0.0),
                "change_pct": quote.get("change_percent", 0.0),
                "available_expirations": exp_list,
                "selected_expiration": target_exp,
                "dte": dte,
                "analytics": {},
                "strikes": [],
                "error": f"No active contracts reported for {symbol} on {target_exp}. Please select another expiration date.",
                "data_source": "yfinance (15m delayed standard equity / options quotes)",
                "retrieved_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            }

        analytics = calculate_chain_analytics(spot_price, dte, calls_df, puts_df)
        strikes_matrix = build_chain_matrix(spot_price, calls_df, puts_df, dte)

        result = {
            "symbol": symbol,
            "name": quote.get("name", symbol),
            "current_price": spot_price,
            "change": quote.get("change", 0.0),
            "change_pct": quote.get("change_percent", 0.0),
            "available_expirations": exp_list,
            "selected_expiration": target_exp,
            "dte": dte,
            "analytics": analytics,
            "strikes": strikes_matrix,
            "data_source": "yfinance (15m delayed standard equity / options quotes)",
            "retrieved_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "bid_ask_sizes": "unavailable (yfinance standard)",
        }

        _store_in_matrix_cache(cache_key, result)
        return result
    except Exception as exc:
        logger.error("Error building options chain matrix for %s (%s): %s", symbol, target_exp, exc)
        return {
            "symbol": symbol,
            "name": quote.get("name", symbol),
            "current_price": spot_price,
            "change": quote.get("change", 0.0),
            "change_pct": quote.get("change_percent", 0.0),
            "available_expirations": exp_list,
            "selected_expiration": target_exp,
            "dte": dte,
            "analytics": {},
            "strikes": [],
            "error": str(exc),
            "data_source": "yfinance (15m delayed standard equity / options quotes)",
            "retrieved_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        }


def get_volatility_cockpit(symbol: str) -> Dict[str, Any]:
    """Calculate institutional-grade Volatility Cockpit: IV Rank, IV Percentile,

    Historical Volatility (21d/60d HV), Volatility Risk Premium (VRP),
    IV Term Structure, 1-Sigma Expected Move Cones, and options playbook regime.
    """
    from data.price_data import get_price_history, get_current_quote
    import numpy as np

    symbol = symbol.strip().upper().replace(".", "-")
    quote = get_current_quote(symbol)
    spot = float(quote.get("current_price", 0.0))
    if spot <= 0:
        return {"symbol": symbol, "error": f"Invalid price for {symbol}"}

    cache_key = f"vol_cockpit_{symbol}"
    if cache_key in _MATRIX_CACHE:
        ts, cached_val = _MATRIX_CACHE[cache_key]
        if time.time() - ts < 180.0:  # 3 minute cache
            return cached_val

    hist = get_price_history(symbol, period="1y")
    if hist is None or len(hist) < 25:
        return {"symbol": symbol, "error": f"Insufficient historical data for {symbol}"}

    # 1. Calculate Realized Historical Volatilities (21d and 60d trading windows)
    returns = np.log(hist["Close"] / hist["Close"].shift(1)).dropna()
    rolling_hv_21 = returns.rolling(window=21).std() * np.sqrt(252) * 100.0
    rolling_hv_60 = returns.rolling(window=60).std() * np.sqrt(252) * 100.0

    valid_hv = rolling_hv_21.dropna()
    current_hv_21 = float(valid_hv.iloc[-1]) if not valid_hv.empty else 25.0
    current_hv_60 = float(rolling_hv_60.dropna().iloc[-1]) if not rolling_hv_60.dropna().empty else current_hv_21
    hv_min = float(valid_hv.min()) if not valid_hv.empty else 15.0
    hv_max = float(valid_hv.max()) if not valid_hv.empty else 60.0

    # 2. Retrieve options term structure & calculate ATM implied volatility
    t = yf.Ticker(symbol)
    exps = getattr(t, "options", [])
    current_iv = current_hv_21 * 1.05
    term_structure = []

    if exps:
        for exp in exps[:8]:
            try:
                ch = t.option_chain(exp)
                c_atm = ch.calls[(ch.calls["strike"] >= spot * 0.93) & (ch.calls["strike"] <= spot * 1.07)]
                p_atm = ch.puts[(ch.puts["strike"] >= spot * 0.93) & (ch.puts["strike"] <= spot * 1.07)]
                iv_series = pd.concat([c_atm["impliedVolatility"], p_atm["impliedVolatility"]]).dropna()
                valid_iv = iv_series[(iv_series > 0.05) & (iv_series < 3.0)] * 100.0
                if not valid_iv.empty:
                    med_val = float(valid_iv.median())
                    d_obj = datetime.strptime(exp, "%Y-%m-%d").date()
                    dte_days = max(0, (d_obj - date.today()).days)
                    term_structure.append({
                        "expiration": exp,
                        "dte": dte_days,
                        "atm_iv_pct": round(med_val, 1),
                    })
            except Exception:
                pass

        # Favor standard cycle (14 - 45 DTE) for headline IV
        standard_terms = [item for item in term_structure if item["dte"] >= 14]
        if standard_terms:
            current_iv = standard_terms[0]["atm_iv_pct"]
        elif term_structure:
            current_iv = term_structure[0]["atm_iv_pct"]

    # 3. Calculate IV Rank & IV Percentile benchmarked against Realized Volatility distribution
    iv_floor = min(hv_min, current_iv * 0.70)
    iv_ceiling = max(hv_max, current_iv * 1.30)
    denom = max(5.0, iv_ceiling - iv_floor)
    iv_rank = max(0.0, min(100.0, ((current_iv - iv_floor) / denom) * 100.0))
    iv_percentile = max(0.0, min(100.0, float((valid_hv < current_iv).mean() * 100.0)))

    # 4. Multi-Horizon 1-Sigma Expected Move Cones
    horizons = [
        ("7d", 7, "1 Week"),
        ("14d", 14, "2 Weeks"),
        ("30d", 30, "1 Month"),
        ("45d", 45, "45-Day Swing"),
        ("60d", 60, "2 Months"),
    ]
    expected_moves = []
    for label_id, days, label_desc in horizons:
        t_yr = days / 365.0
        em_dollar = spot * (current_iv / 100.0) * np.sqrt(t_yr)
        em_pct = (em_dollar / spot) * 100.0
        expected_moves.append({
            "id": label_id,
            "label": label_desc,
            "days": days,
            "expected_move": round(float(em_dollar), 2),
            "expected_move_pct": round(float(em_pct), 2),
            "lower_cone": round(float(spot - em_dollar), 2),
            "upper_cone": round(float(spot + em_dollar), 2),
        })

    # 5. Volatility Regime and Playbook
    if iv_rank < 30.0:
        regime = "LOW_VOLATILITY"
        regime_title = "Low Volatility Environment"
        regime_badge = "IV Discount (Cheap Premium)"
        regime_color = "emerald"
        playbook = [
            "Long Calls/Puts and Vertical Debit Spreads favored (volatility premium is cheap).",
            "Avoid selling raw premium or unhedged credit spreads due to compressed yield.",
            "Long gamma & vega positioning offers asymmetric upside if volatility explodes.",
        ]
    elif iv_rank > 65.0:
        regime = "HIGH_VOLATILITY"
        regime_title = "High Volatility Environment"
        regime_badge = "IV Rich (Elevated Premium)"
        regime_color = "rose"
        playbook = [
            "Credit Spreads, Iron Condors & Covered Calls favored to harvest rich extrinsic decay.",
            "Avoid buying high-priced OTM options prone to post-catalyst IV crush.",
            "Vega risk is negative; contract positions benefit as implied volatility normalizes.",
        ]
    else:
        regime = "MODERATE_VOLATILITY"
        regime_title = "Moderate Volatility Environment"
        regime_badge = "Fair Volatility Premium"
        regime_color = "cyan"
        playbook = [
            "Directional vertical debit spreads (0.35-0.50 Delta) offer balanced risk/reward.",
            "Calendar spreads or diagonal spreads capture term structure differentials.",
            "Monitor upcoming earnings and macro catalysts for volatility inflection points.",
        ]

    # 6. Volatility Risk Premium (VRP = IV / HV)
    vrp_ratio = round(current_iv / max(1.0, current_hv_21), 2)
    vrp_desc = (
        "IV Trading at Premium over Realized Vol"
        if vrp_ratio > 1.05
        else ("IV Discounted relative to Realized Vol" if vrp_ratio < 0.95 else "IV Fairly Valued vs Realized Vol")
    )

    retrieved_at_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    result = {
        "symbol": symbol,
        "name": quote.get("name", symbol),
        "current_price": round(spot, 2),
        "change": round(float(quote.get("change", 0.0)), 2),
        "change_pct": round(float(quote.get("change_percent", 0.0)), 2),
        "current_iv": round(current_iv, 1),
        "current_hv_21d": round(current_hv_21, 1),
        "current_hv_60d": round(current_hv_60, 1),
        "iv_rank": round(iv_rank, 1),
        "iv_percentile": round(iv_percentile, 1),
        "hv_benchmarked_iv_rank": round(iv_rank, 1),
        "hv_benchmarked_iv_percentile": round(iv_percentile, 1),
        "metric_methodology": "Realized Volatility Benchmark (Current ATM IV scaled against 1-Year 21-Day Historical Realized Volatility window; yfinance free tier lacks historical IV series)",
        "methodology_disclaimer": "Note: Realized Volatility Benchmark is used because standard free data providers do not store historical implied volatility time series. True 52-week IV Rank requires historical options exchange archives.",
        "data_source": "yfinance (15m delayed standard equity / options quotes)",
        "retrieved_at_utc": retrieved_at_utc,
        "last_trade_time": quote.get("last_trade_time", "unavailable"),
        "bid_ask_sizes": "unavailable (yfinance standard)",
        "iv_floor": round(iv_floor, 1),
        "iv_ceiling": round(iv_ceiling, 1),
        "hv_min_1y": round(hv_min, 1),
        "hv_max_1y": round(hv_max, 1),
        "vrp_ratio": vrp_ratio,
        "vrp_desc": vrp_desc,
        "regime": regime,
        "regime_title": regime_title,
        "regime_badge": regime_badge,
        "regime_color": regime_color,
        "playbook": playbook,
        "term_structure": term_structure,
        "expected_moves": expected_moves,
    }

    _store_in_matrix_cache(cache_key, result)
    return result
