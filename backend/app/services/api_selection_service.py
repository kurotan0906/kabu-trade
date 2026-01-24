"""API selection service (collection + gate evaluation + policy checks).

This module intentionally avoids handling secrets. It operates on non-secret schemas
and produces structured evaluation outputs that can later be persisted or exported.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from app.schemas.api_selection import (
    AccessTier,
    ApiCandidate,
    CandidateEvaluation,
    CriterionEvaluation,
    CriterionKey,
    EvaluationCriteriaSet,
    GatePolicy,
    MarketScope,
    Verdict,
)


@dataclass(frozen=True)
class PrimarySourcePolicy:
    """一次情報の記録ポリシー。

    - 公式ドキュメントURLと確認日は必須（URL不明は「要確認」扱い）
    """

    require_url: bool = True


def evaluate_gate(
    *,
    candidate: ApiCandidate,
    required_market_scope: MarketScope,
    gate: GatePolicy,
) -> tuple[Verdict, List[str]]:
    reasons: List[str] = []
    missing_info = False
    freshness_failed = False

    # Prime market requirement
    if gate.require_prime_market:
        if not candidate.market_coverage:
            reasons.append("市場カバレッジが未記録のため、プライム要件を判定できません")
            missing_info = True
        elif required_market_scope == MarketScope.JPX_PRIME and not candidate.market_coverage.supports_required_scope:
            reasons.append("日本のプライム市場対応の要件を満たしません")

    # Free start requirement
    if gate.require_free_start:
        if not candidate.pricing:
            reasons.append("料金体系が未記録のため、無料開始要件を判定できません")
            missing_info = True
        elif candidate.pricing.access_tier not in (AccessTier.FREE, AccessTier.FREE_TRIAL):
            reasons.append("無料プラン/無料トライアルで開始できません")

    # Freshness requirement (Requirement 2.6)
    if gate.require_fresh_data:
        if not candidate.freshness or candidate.freshness.max_delay_days is None:
            reasons.append("データ鮮度が未記録のため、鮮度要件を判定できません")
            missing_info = True
        else:
            if candidate.freshness.max_delay_days > gate.max_delay_days:
                reasons.append(
                    f"データ鮮度要件を満たしません（遅延={candidate.freshness.max_delay_days}日 > 許容={gate.max_delay_days}日）"
                )
                freshness_failed = True
            if candidate.freshness.recent_data_gap_days and candidate.freshness.recent_data_gap_days > 0:
                reasons.append(
                    f"直近データの欠落が疑われます（欠落={candidate.freshness.recent_data_gap_days}日）"
                )
                freshness_failed = True

    if reasons:
        # Unknown vs Fail: if information is missing, default to HOLD to avoid false PASS.
        if missing_info:
            return Verdict.HOLD, reasons

        # If only freshness is failing but free-start is satisfied, keep as HOLD to force
        # explicit fallback planning (Requirement 3.4) instead of a silent rejection.
        if (
            freshness_failed
            and gate.require_free_start
            and candidate.pricing
            and candidate.pricing.access_tier in (AccessTier.FREE, AccessTier.FREE_TRIAL)
        ):
            return Verdict.HOLD, reasons + ["無料開始は満たすが鮮度未達のため、フォールバック案が必要です"]

        return Verdict.FAIL, reasons

    return Verdict.PASS, []


def check_terms_conflict(
    *,
    candidate: ApiCandidate,
    requires_redistribution: bool,
) -> Optional[str]:
    """利用規約の矛盾を簡易判定する。

    - 再配布が必要なのに、候補が再配布不可を明記している場合は矛盾。
    - 不明の場合は矛盾の可否を確定できないため、None を返す。
    """

    if not candidate.terms or candidate.terms.redistribution_allowed is None:
        return None

    if requires_redistribution and candidate.terms.redistribution_allowed is False:
        return "再配布が必要だが、候補APIの規約で再配布が禁止されています"

    return None


def build_candidate_evaluation(
    *,
    candidate: ApiCandidate,
    criteria_set: EvaluationCriteriaSet,
    required_market_scope: MarketScope,
    checked_at: date,
    requires_redistribution: bool = False,
    primary_source_policy: PrimarySourcePolicy = PrimarySourcePolicy(),
) -> CandidateEvaluation:
    """候補1件の評価（ゲート条件 + 規約矛盾の反映）を構築する。"""

    gate_verdict, gate_reasons = evaluate_gate(
        candidate=candidate,
        required_market_scope=required_market_scope,
        gate=criteria_set.gate,
    )

    results: List[CriterionEvaluation] = []

    # Terms conflict (Requirement 2.4): represented as a criterion result.
    conflict = check_terms_conflict(
        candidate=candidate,
        requires_redistribution=requires_redistribution,
    )
    if conflict:
        results.append(
            CriterionEvaluation(
                criterion_key=CriterionKey.TERMS,
                verdict=Verdict.FAIL,
                summary=conflict,
                evidence=candidate.terms.evidence if candidate.terms else None,
            )
        )

    # Primary source check: if policy requires URL but evidence URL missing, mark HOLD.
    if primary_source_policy.require_url:
        evidence_urls = []
        if candidate.market_coverage and candidate.market_coverage.evidence and candidate.market_coverage.evidence.url:
            evidence_urls.append(str(candidate.market_coverage.evidence.url))
        if candidate.pricing and candidate.pricing.evidence and candidate.pricing.evidence.url:
            evidence_urls.append(str(candidate.pricing.evidence.url))
        if candidate.terms and candidate.terms.evidence and candidate.terms.evidence.url:
            evidence_urls.append(str(candidate.terms.evidence.url))
        if not evidence_urls:
            results.append(
                CriterionEvaluation(
                    criterion_key=CriterionKey.OTHER,
                    verdict=Verdict.HOLD,
                    summary="一次情報URLが未記録のため、根拠の追試ができません",
                )
            )

            if gate_verdict == Verdict.PASS:
                gate_verdict = Verdict.HOLD
                gate_reasons = gate_reasons + ["一次情報URLが未記録のため保留"]

    disclosure_notes: List[str] = []
    if candidate.freshness and candidate.freshness.max_delay_days is not None:
        if candidate.freshness.max_delay_days > 0:
            disclosure_notes.append(f"データが最大{candidate.freshness.max_delay_days}日遅延する可能性があります")
    if candidate.freshness and candidate.freshness.recent_data_gap_days:
        disclosure_notes.append(f"直近データが欠落する可能性があります（欠落={candidate.freshness.recent_data_gap_days}日）")
    if candidate.corporate_actions:
        if candidate.corporate_actions.adjusted_prices_available is None:
            disclosure_notes.append("株価が調整済み/未調整のどちらか不明です（分割/併合の影響に注意）")
        elif candidate.corporate_actions.adjusted_prices_available is False:
            disclosure_notes.append("株価は未調整の可能性があります（分割/併合で過去価格が不連続になる可能性）")

    fallback_plan: Optional[str] = None
    if any("フォールバック案が必要" in r for r in gate_reasons):
        fallback_plan = "（要作成）直近データのみ別APIで補完する/段階的に有償プランへ移行する等を検討"

    return CandidateEvaluation(
        candidate=candidate,
        gate_verdict=gate_verdict,
        gate_reasons=gate_reasons,
        criteria_results=results,
        disclosure_notes=disclosure_notes,
        fallback_plan=fallback_plan,
        checked_at=checked_at,
    )

