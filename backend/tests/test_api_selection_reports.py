from datetime import date

from app.schemas.api_selection import (
    AccessTier,
    ApiCandidate,
    AuthMethod,
    CandidateEvaluation,
    CriterionEvaluation,
    CriterionKey,
    EvidenceRef,
    MarketCoverage,
    MarketScope,
    PricingSummary,
    Verdict,
)
from app.services.api_selection_reports import (
    DecisionInput,
    RiskItem,
    render_candidate_matrix_markdown,
    render_decision_record_markdown,
    render_risk_register_markdown,
)


def test_candidate_matrix_includes_gate_verdict_and_evidence():
    c = ApiCandidate(
        provider="JPX",
        name="J-Quants API",
        auth_method=AuthMethod.API_KEY,
        market_coverage=MarketCoverage(
            scope=MarketScope.JPX_ALL,
            supports_required_scope=True,
            evidence=EvidenceRef(source_name="doc", checked_at=date(2026, 1, 1)),
        ),
        pricing=PricingSummary(access_tier=AccessTier.FREE),
    )
    ev = CandidateEvaluation(
        candidate=c,
        gate_verdict=Verdict.PASS,
        gate_reasons=[],
        criteria_results=[
            CriterionEvaluation(
                criterion_key=CriterionKey.TERMS,
                verdict=Verdict.HOLD,
                summary="要確認",
                evidence=EvidenceRef(source_name="terms", checked_at=date(2026, 1, 2)),
            )
        ],
        checked_at=date(2026, 1, 2),
    )

    md = render_candidate_matrix_markdown([ev])
    assert "CandidateMatrix" in md
    assert "PASS" in md
    assert "doc / 2026-01-01" in md
    assert "terms / 2026-01-02" in md


def test_decision_record_contains_selected_and_prereqs():
    c = ApiCandidate(provider="JPX", name="J-Quants API", auth_method=AuthMethod.API_KEY)
    md = render_decision_record_markdown(
        DecisionInput(
            selected=[c],
            rejected=[],
            selected_reasons=["無料で開始できる"],
            rejected_reasons=[],
            prerequisites=["JQUANTS_ID_TOKEN を設定する（値は記録しない）"],
        ),
        decided_at=date(2026, 1, 3),
    )
    assert "DecisionRecord" in md
    assert "JPX / J-Quants API" in md
    assert "JQUANTS_ID_TOKEN" in md


def test_risk_register_renders_table():
    md = render_risk_register_markdown(
        [
            RiskItem(
                title="料金変動",
                impact="月額コスト増加の可能性",
                mitigation="代替候補を保持し、定期的に見直す",
                evidence=EvidenceRef(source_name="pricing", checked_at=date(2026, 1, 4)),
            )
        ],
        created_at=date(2026, 1, 4),
    )
    assert "RiskRegister" in md
    assert "料金変動" in md
    assert "pricing / 2026-01-04" in md

