from datetime import date

import pytest

from app.schemas.api_selection import EvidenceRef
from app.services.api_selection_maintenance import (
    EvidenceStatus,
    FatalReevaluationTrigger,
    UpdateHistoryEntry,
    append_update_history,
    detect_stale_evidence,
    should_trigger_fatal_reevaluation,
)
from app.schemas.api_selection import FreshnessSummary, GatePolicy


def test_detect_stale_evidence_flags_old_entries():
    evidences = [
        EvidenceRef(source_name="doc", checked_at=date(2025, 1, 1)),
        EvidenceRef(source_name="doc2", checked_at=date(2026, 1, 20)),
    ]
    res = detect_stale_evidence(evidences, today=date(2026, 1, 24), stale_after_days=90)
    assert any(r.status == EvidenceStatus.STALE and r.evidence.source_name == "doc" for r in res)


def test_append_update_history_keeps_newest_first():
    h1 = UpdateHistoryEntry(updated_at=date(2026, 1, 1), change_summary="a", impact_summary="i")
    h2 = UpdateHistoryEntry(updated_at=date(2026, 1, 2), change_summary="b", impact_summary="i")
    merged = append_update_history([h1], h2)
    assert merged[0].updated_at == date(2026, 1, 2)


def test_should_trigger_fatal_reevaluation_when_freshness_changes():
    gate = GatePolicy(max_delay_days=5)
    prev = FreshnessSummary(max_delay_days=1, recent_data_gap_days=None)
    cur = FreshnessSummary(max_delay_days=2, recent_data_gap_days=None)
    res = should_trigger_fatal_reevaluation(previous=prev, current=cur, gate=gate)
    assert isinstance(res, FatalReevaluationTrigger)
    assert res.required is True


def test_should_trigger_fatal_reevaluation_when_delay_exceeds_gate():
    gate = GatePolicy(max_delay_days=5)
    prev = FreshnessSummary(max_delay_days=1, recent_data_gap_days=None)
    cur = FreshnessSummary(max_delay_days=30, recent_data_gap_days=None)
    res = should_trigger_fatal_reevaluation(previous=prev, current=cur, gate=gate)
    assert res.required is True

