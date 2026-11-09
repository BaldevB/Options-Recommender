"""Shared test fixtures: keep tests offline and away from the real recommendation journal."""

import pytest


@pytest.fixture(autouse=True)
def _isolate_edge_model(tmp_path, monkeypatch):
    monkeypatch.setenv("REC_JOURNAL_PATH", str(tmp_path / "rec_journal.sqlite"))
    monkeypatch.setenv("REC_JOURNAL_EVAL_ENABLED", "0")
    monkeypatch.setattr("options.edge.get_risk_free_rate", lambda: 0.045)
    monkeypatch.setattr("options.edge.get_dividend_yield", lambda symbol, spot: 0.0)
    from analysis import rec_journal
    rec_journal._CAL_CACHE.update({"ts": 0.0, "report": None})
    # Live-feed results are cached module-wide; never let one test's result leak into the next
    import api
    api._LIVE_OPTIONS_CACHE.update({"timestamp": 0.0, "items": []})
    api._LIVE_OPTIONS_STATUS.update({"state": "unknown", "checked_at": 0.0, "symbols_screened": 0, "message": ""})
    api._HIGH_CONF_CACHE.clear()
    yield
