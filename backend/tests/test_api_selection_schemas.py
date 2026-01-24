from datetime import date

import pytest

from app.schemas.api_selection import (
    AccessTier,
    ApiCandidate,
    AuthMethod,
    CandidateEvaluation,
    CriterionDefinition,
    CriterionEvaluation,
    CriterionKey,
    EvidenceRef,
    EvaluationCriteriaSet,
    GatePolicy,
    MarketCoverage,
    MarketScope,
    PricingSummary,
    TermsSummary,
    Verdict,
)


def test_api_candidate_does_not_require_secrets():
    candidate = ApiCandidate(
        provider="JPX",
        name="J-Quants API",
        auth_method=AuthMethod.API_KEY,
        supported_data=[],
        market_coverage=MarketCoverage(
            scope=MarketScope.JPX_ALL,
            supports_required_scope=True,
            evidence=EvidenceRef(
                source_name="example",
                checked_at=date(2026, 1, 1),
            ),
        ),
        pricing=PricingSummary(access_tier=AccessTier.FREE),
        terms=TermsSummary(redistribution_allowed=None),
    )
    assert candidate.provider == "JPX"


def test_criteria_set_contains_gate_policy_defaults():
    criteria = EvaluationCriteriaSet()
    assert criteria.gate.require_prime_market is True
    assert criteria.gate.require_free_start is True
    assert criteria.gate.require_fresh_data is True
    assert criteria.gate.max_delay_days == 5


def test_candidate_evaluation_can_reference_evidence():
    criteria_def = CriterionDefinition(
        key=CriterionKey.COST,
        title="コスト",
        method="doc_review",
        minimum_condition="無料プランまたは無料トライアルでPoC可能であること",
        evidence_required=True,
    )
    criteria_set = EvaluationCriteriaSet(gate=GatePolicy(), criteria=[criteria_def])

    candidate = ApiCandidate(provider="X", name="Y", auth_method=AuthMethod.NONE)
    eval_item = CandidateEvaluation(
        candidate=candidate,
        gate_verdict=Verdict.PASS,
        gate_reasons=[],
        criteria_results=[
            CriterionEvaluation(
                criterion_key=CriterionKey.COST,
                verdict=Verdict.PASS,
                evidence=EvidenceRef(source_name="example", checked_at=date(2026, 1, 2)),
            )
        ],
        checked_at=date(2026, 1, 2),
    )

    assert criteria_set.criteria[0].key == CriterionKey.COST
    assert eval_item.criteria_results[0].evidence is not None

