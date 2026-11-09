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
    yield
