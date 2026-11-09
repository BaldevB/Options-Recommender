"""Recommendation journal: record every options idea, score it later, and measure calibration.

Without outcomes, "accuracy" can't be measured. This module:
- records each recommendation (contract, entry mid, predicted probability, signal confidence, exits),
- evaluates it later against the option's actual daily prices (target hit, stop hit, or time exit)
  and the underlying's directional return after 5/10/21 trading days,
- reports calibration: predicted vs realized win rate by bucket, Brier score, win rate by confidence.

Storage is a small SQLite file (REC_JOURNAL_PATH, default .data/rec_journal.sqlite). On hosts with
ephemeral disks (e.g. Render free tier) point REC_JOURNAL_PATH at a persistent volume.
"""

from __future__ import annotations

import logging
import os
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Dict, Iterator, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()
_LAST_EVAL_TS = 0.0
MIN_EVAL_INTERVAL_SEC = 30 * 60
MAX_TRACK_DAYS = 45            # stop tracking after this many calendar days
MIN_BUCKET_SAMPLES = 20        # calibrated win rates are only reported for buckets this large
HORIZONS = (5, 10, 21)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    created_date TEXT NOT NULL,
    source TEXT,
    symbol TEXT NOT NULL,
    contract TEXT NOT NULL,
    option_type TEXT,
    strike REAL,
    expiration TEXT,
    bias TEXT,
    spot REAL,
    entry_mid REAL,
    target_px REAL,
    stop_px REAL,
    max_hold_days INTEGER,
    signal_confidence REAL,
    pred_prob_profit REAL,
    pred_prob_target REAL,
    pred_expected_return_pct REAL,
    edge_score REAL,
    rank_score REAL,
    pop_method TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING',
    outcome TEXT,
    exit_px REAL,
    pnl_per_contract REAL,
    days_held INTEGER,
    ret_5d REAL,
    ret_10d REAL,
    ret_21d REAL,
    evaluated_at TEXT,
    UNIQUE(contract, created_date)
);
"""


def journal_path() -> str:
    default = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".data", "rec_journal.sqlite")
    return os.environ.get("REC_JOURNAL_PATH", default)


def journal_enabled() -> bool:
    return os.environ.get("REC_JOURNAL_ENABLED", "1").lower() in ("1", "true", "yes")


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    path = journal_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute(_SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def _num(v: Any) -> Optional[float]:
    try:
        f = float(v)
        return f if f == f else None  # drop NaN
    except (TypeError, ValueError):
        return None


def record_recommendations(items: List[Dict[str, Any]], source: str = "") -> int:
    """Record recommendations (one row per contract per day). Never raises; returns rows inserted."""
    if not items or not journal_enabled():
        return 0
    now = datetime.now(timezone.utc)
    rows = []
    for it in items:
        contract = str(it.get("contract") or "").strip().upper()
        symbol = str(it.get("symbol") or "").strip().upper()
        entry = _num(it.get("entry_mid"))
        if not contract or not symbol or not entry or entry <= 0:
            continue
        rows.append((
            now.isoformat(), now.date().isoformat(), source, symbol, contract,
            it.get("option_type"), _num(it.get("strike")), it.get("expiration"), it.get("bias"),
            _num(it.get("spot")), entry, _num(it.get("target_px")) or round(entry * 1.5, 2),
            _num(it.get("stop_px")) or round(entry * 0.5, 2), int(it.get("max_hold_days") or 12),
            _num(it.get("signal_confidence")), _num(it.get("pred_prob_profit")), _num(it.get("pred_prob_target")),
            _num(it.get("pred_expected_return_pct")), _num(it.get("edge_score")), _num(it.get("rank_score")),
            it.get("pop_method"),
        ))
    if not rows:
        return 0
    try:
        with _LOCK, _connect() as conn:
            cur = conn.executemany(
                """INSERT OR IGNORE INTO recommendations (
                    created_at, created_date, source, symbol, contract, option_type, strike, expiration, bias,
                    spot, entry_mid, target_px, stop_px, max_hold_days, signal_confidence, pred_prob_profit,
                    pred_prob_target, pred_expected_return_pct, edge_score, rank_score, pop_method
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                rows,
            )
            return cur.rowcount or 0
    except Exception as exc:
        logger.warning("Recommendation journal write failed: %s", exc)
        return 0


def suggestion_to_journal_item(sug: Any, symbol: str, bias: str, confidence: float) -> Dict[str, Any]:
    """Map an options.suggester.OptionSuggestion to a journal row."""
    tp = getattr(sug, "trade_plan", None)
    return {
        "symbol": symbol,
        "contract": sug.contract_symbol,
        "option_type": sug.option_type,
        "strike": sug.strike,
        "expiration": sug.expiration,
        "bias": bias,
        "spot": sug.spot_price,
        "entry_mid": sug.mid_price,
        "target_px": getattr(tp, "tp1_option_price", None),
        "stop_px": getattr(tp, "stop_loss_option_price", None),
        "max_hold_days": getattr(tp, "max_holding_period_days", 12),
        "signal_confidence": confidence,
        "pred_prob_profit": getattr(tp, "probability_of_profit_pct", None),
        "pred_prob_target": getattr(tp, "prob_target_before_stop_pct", None),
        "pred_expected_return_pct": getattr(tp, "expected_return_pct", None),
        "edge_score": getattr(sug, "edge_score", None),
        "rank_score": getattr(sug, "rank_score", None),
        "pop_method": getattr(tp, "pop_method", None),
    }


# --------------------------------------------------------------------------------------
# Evaluation
# --------------------------------------------------------------------------------------

HistoryFetcher = Callable[[str, date], Optional[pd.DataFrame]]


def _yf_history(symbol: str, start: date) -> Optional[pd.DataFrame]:
    import yfinance as yf
    df = yf.Ticker(symbol).history(start=start.isoformat(), interval="1d", auto_adjust=False)
    return df if df is not None and not df.empty else None


def evaluate_option_path(
    bars: Optional[pd.DataFrame], created: date, target: float, stop: float, max_hold: int,
    expiration: Optional[date], today: date,
) -> Optional[Dict[str, Any]]:
    """Walk daily option bars after the recommendation day. Same-day target+stop counts as a stop (conservative)."""
    if bars is None or bars.empty:
        return None
    idx = pd.to_datetime(bars.index)
    after = bars[[d.date() > created for d in idx]]
    days = 0
    for ts, bar in after.iterrows():
        days += 1
        low, high, close = float(bar.get("Low", 0) or 0), float(bar.get("High", 0) or 0), float(bar.get("Close", 0) or 0)
        if low > 0 and low <= stop:
            return {"outcome": "STOP", "exit_px": stop, "days_held": days}
        if high >= target:
            return {"outcome": "TARGET", "exit_px": target, "days_held": days}
        if days >= max_hold:
            return {"outcome": "TIME_EXIT", "exit_px": close, "days_held": days}
    expired = expiration is not None and today > expiration
    stale = (today - created).days > MAX_TRACK_DAYS
    if (expired or stale) and len(after) > 0:
        return {"outcome": "TIME_EXIT", "exit_px": float(after["Close"].iloc[-1]), "days_held": days}
    if expired and len(after) == 0:
        return {"outcome": "NO_DATA", "exit_px": None, "days_held": 0}
    return None


def _directional_returns(bars: Optional[pd.DataFrame], created: date, bias: str) -> Dict[str, Optional[float]]:
    out: Dict[str, Optional[float]] = {f"ret_{h}d": None for h in HORIZONS}
    if bars is None or bars.empty:
        return out
    idx = pd.to_datetime(bars.index)
    on_or_before = bars[[d.date() <= created for d in idx]]
    after = bars[[d.date() > created for d in idx]]
    if on_or_before.empty:
        return out
    base = float(on_or_before["Close"].iloc[-1])
    sign = -1.0 if str(bias).upper() == "BEARISH" else 1.0
    for h in HORIZONS:
        if len(after) >= h and base > 0:
            out[f"ret_{h}d"] = round(sign * (float(after["Close"].iloc[h - 1]) / base - 1.0) * 100.0, 2)
    return out


def evaluate_pending(fetch: Optional[HistoryFetcher] = None, today: Optional[date] = None, limit: int = 60) -> Dict[str, int]:
    """Score pending recommendations against real prices. Network errors leave rows pending."""
    fetch = fetch or _yf_history
    today = today or datetime.now(timezone.utc).date()
    stats = {"checked": 0, "resolved": 0, "errors": 0}
    with _LOCK, _connect() as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT * FROM recommendations WHERE status != 'DONE' AND created_date < ? ORDER BY created_at LIMIT ?",
            (today.isoformat(), limit),
        )]
    underlying_cache: Dict[str, Optional[pd.DataFrame]] = {}
    updates = []
    for r in rows:
        stats["checked"] += 1
        created = date.fromisoformat(r["created_date"])
        exp = date.fromisoformat(r["expiration"][:10]) if r.get("expiration") else None
        try:
            res = r if r["status"] == "SCORED" else None
            if res is None:
                res = evaluate_option_path(
                    fetch(r["contract"], created), created, float(r["target_px"]), float(r["stop_px"]),
                    int(r["max_hold_days"] or 12), exp, today,
                )
            if r["symbol"] not in underlying_cache:
                underlying_cache[r["symbol"]] = fetch(r["symbol"], created - timedelta(days=7))
            rets = _directional_returns(underlying_cache[r["symbol"]], created, r.get("bias") or "")
        except Exception as exc:
            stats["errors"] += 1
            logger.debug("Journal evaluation failed for %s: %s", r["contract"], exc)
            continue
        if res is None:
            if any(v is not None for v in rets.values()):
                updates.append(("PENDING", None, None, None, None, rets, r["id"]))
            continue
        all_horizons = all(rets[f"ret_{h}d"] is not None for h in HORIZONS)
        too_old = (today - created).days > MAX_TRACK_DAYS
        status = "DONE" if (all_horizons or too_old) else "SCORED"
        exit_px = res.get("exit_px")
        pnl = round((exit_px - float(r["entry_mid"])) * 100.0, 2) if exit_px is not None else None
        updates.append((status, res.get("outcome"), exit_px, pnl, res.get("days_held"), rets, r["id"]))
        stats["resolved"] += 1 if r["status"] == "PENDING" else 0
    if updates:
        now = datetime.now(timezone.utc).isoformat()
        with _LOCK, _connect() as conn:
            for status, outcome, exit_px, pnl, days, rets, rid in updates:
                if outcome is None:
                    conn.execute(
                        "UPDATE recommendations SET ret_5d=COALESCE(?,ret_5d), ret_10d=COALESCE(?,ret_10d), "
                        "ret_21d=COALESCE(?,ret_21d) WHERE id=?",
                        (rets["ret_5d"], rets["ret_10d"], rets["ret_21d"], rid),
                    )
                else:
                    conn.execute(
                        "UPDATE recommendations SET status=?, outcome=COALESCE(outcome, ?), exit_px=COALESCE(exit_px, ?), "
                        "pnl_per_contract=COALESCE(pnl_per_contract, ?), days_held=COALESCE(days_held, ?), "
                        "ret_5d=COALESCE(?,ret_5d), ret_10d=COALESCE(?,ret_10d), ret_21d=COALESCE(?,ret_21d), "
                        "evaluated_at=? WHERE id=?",
                        (status, outcome, exit_px, pnl, days, rets["ret_5d"], rets["ret_10d"], rets["ret_21d"], now, rid),
                    )
    return stats


def maybe_evaluate(force: bool = False) -> Optional[Dict[str, int]]:
    """Rate-limited evaluation (at most every 30 minutes unless forced)."""
    global _LAST_EVAL_TS
    if not journal_enabled():
        return None
    if not force and time.time() - _LAST_EVAL_TS < MIN_EVAL_INTERVAL_SEC:
        return None
    _LAST_EVAL_TS = time.time()
    try:
        return evaluate_pending()
    except Exception as exc:
        logger.warning("Journal evaluation run failed: %s", exc)
        return None


# --------------------------------------------------------------------------------------
# Calibration report
# --------------------------------------------------------------------------------------

PROB_BUCKETS = [(0, 30), (30, 40), (40, 50), (50, 60), (60, 101)]
CONF_BUCKETS = [(0.0, 0.25), (0.25, 0.45), (0.45, 0.65), (0.65, 1.01)]


def _load_scored() -> pd.DataFrame:
    with _LOCK, _connect() as conn:
        return pd.read_sql_query(
            "SELECT * FROM recommendations WHERE outcome IN ('TARGET','STOP','TIME_EXIT')", conn
        )


def calibration_report() -> Dict[str, Any]:
    """Predicted vs realized outcomes. 'win' = trade closed with a profit under the plan's exits."""
    with _LOCK, _connect() as conn:
        counts = {row[0]: row[1] for row in conn.execute("SELECT status, COUNT(*) FROM recommendations GROUP BY status")}
    df = _load_scored()
    report: Dict[str, Any] = {
        "total_recorded": int(sum(counts.values())),
        "pending": int(counts.get("PENDING", 0)),
        "scored": int(len(df)),
        "min_bucket_samples": MIN_BUCKET_SAMPLES,
        "journal_path": journal_path(),
    }
    if df.empty:
        report.update({"win_rate_pct": None, "brier_score": None, "by_predicted_probability": [], "by_signal_confidence": []})
        return report

    df["win"] = (df["pnl_per_contract"].fillna(0) > 0).astype(float)
    report["win_rate_pct"] = round(df["win"].mean() * 100.0, 1)
    report["avg_pnl_per_contract"] = round(float(df["pnl_per_contract"].mean()), 2)
    report["outcomes"] = df["outcome"].value_counts().to_dict()
    pred = df["pred_prob_profit"].astype(float) / 100.0
    has_pred = pred.notna()
    report["brier_score"] = round(float(((pred[has_pred] - df.loc[has_pred, "win"]) ** 2).mean()), 4) if has_pred.any() else None
    report["avg_predicted_prob_pct"] = round(float(pred[has_pred].mean() * 100.0), 1) if has_pred.any() else None

    by_prob = []
    for lo, hi in PROB_BUCKETS:
        sub = df[(df["pred_prob_profit"] >= lo) & (df["pred_prob_profit"] < hi)]
        if len(sub):
            by_prob.append({
                "bucket": f"{lo}-{min(hi, 100)}%", "n": int(len(sub)),
                "avg_predicted_pct": round(float(sub["pred_prob_profit"].mean()), 1),
                "realized_win_rate_pct": round(float(sub["win"].mean() * 100.0), 1),
                "reliable": bool(len(sub) >= MIN_BUCKET_SAMPLES),
            })
    report["by_predicted_probability"] = by_prob

    by_conf = []
    for lo, hi in CONF_BUCKETS:
        sub = df[(df["signal_confidence"] >= lo) & (df["signal_confidence"] < hi)]
        if len(sub):
            by_conf.append({
                "bucket": f"{lo:.2f}-{min(hi, 1.0):.2f}", "n": int(len(sub)),
                "realized_win_rate_pct": round(float(sub["win"].mean() * 100.0), 1),
                "avg_directional_ret_10d_pct": round(float(sub["ret_10d"].mean()), 2) if sub["ret_10d"].notna().any() else None,
                "reliable": bool(len(sub) >= MIN_BUCKET_SAMPLES),
            })
    report["by_signal_confidence"] = by_conf
    return report


_CAL_CACHE: Dict[str, Any] = {"ts": 0.0, "report": None}


def calibrated_win_rate(pred_prob_pct: Optional[float]) -> Optional[float]:
    """Realized win rate of past recommendations with a similar predicted probability (None until enough data)."""
    if pred_prob_pct is None or not journal_enabled():
        return None
    try:
        if time.time() - _CAL_CACHE["ts"] > 600 or _CAL_CACHE["report"] is None:
            _CAL_CACHE["report"] = calibration_report()
            _CAL_CACHE["ts"] = time.time()
        for b in _CAL_CACHE["report"].get("by_predicted_probability", []):
            lo, hi = (float(x) for x in b["bucket"].rstrip("%").split("-"))
            if lo <= pred_prob_pct < (hi if hi < 100 else 101) and b["reliable"]:
                return b["realized_win_rate_pct"]
    except Exception as exc:
        logger.debug("Calibration lookup failed: %s", exc)
    return None
