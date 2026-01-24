"""Report generators for API selection outputs (markdown).

These functions intentionally avoid including any secrets. They only use non-secret
schemas and include evidence references (source + date + URL) for reproducibility.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Iterable, List, Optional

from app.schemas.api_selection import (
    ApiCandidate,
    CandidateEvaluation,
    CriterionEvaluation,
    CriterionKey,
    EvidenceRef,
    Verdict,
)


def _verdict_label(v: Verdict) -> str:
    return {
        Verdict.PASS: "PASS",
        Verdict.FAIL: "FAIL",
        Verdict.HOLD: "HOLD",
        Verdict.UNKNOWN: "UNKNOWN",
    }.get(v, "UNKNOWN")


def _format_evidence(e: Optional[EvidenceRef]) -> str:
    if not e:
        return "-"
    url = f" ({e.url})" if e.url else ""
    return f"{e.source_name} / {e.checked_at.isoformat()}{url}"


def render_candidate_matrix_markdown(evaluations: Iterable[CandidateEvaluation]) -> str:
    """Generate a CandidateMatrix markdown summary.

    Includes:
    - gate verdict + reasons
    - per-criterion verdicts (when present in CandidateEvaluation.criteria_results)
    - evidence references where available
    """

    ev_list = list(evaluations)
    lines: List[str] = []
    lines.append("# CandidateMatrix")
    lines.append("")
    lines.append("## サマリ")
    lines.append("")
    lines.append("| 候補 | ゲート判定 | 理由 | 根拠 |")
    lines.append("|------|----------|------|------|")
    for ev in ev_list:
        c = ev.candidate
        name = f"{c.provider} / {c.name}"
        reasons = " / ".join(ev.gate_reasons) if ev.gate_reasons else "-"
        evidence = "-"
        if c.market_coverage and c.market_coverage.evidence:
            evidence = _format_evidence(c.market_coverage.evidence)
        elif c.pricing and c.pricing.evidence:
            evidence = _format_evidence(c.pricing.evidence)
        elif c.terms and c.terms.evidence:
            evidence = _format_evidence(c.terms.evidence)
        lines.append(f"| {name} | {_verdict_label(ev.gate_verdict)} | {reasons} | {evidence} |")

    # Detail section (criteria)
    lines.append("")
    lines.append("## 詳細（評価軸）")
    lines.append("")
    lines.append("> `criteria_results` にあるもののみ表示します（未評価は表に出しません）。")
    lines.append("")

    for ev in ev_list:
        c = ev.candidate
        lines.append(f"### {c.provider} / {c.name}")
        lines.append("")
        if ev.disclosure_notes:
            lines.append("- 注意事項:")
            for n in ev.disclosure_notes:
                lines.append(f"  - {n}")
            lines.append("")
        if ev.fallback_plan:
            lines.append(f"- フォールバック案: {ev.fallback_plan}")
            lines.append("")
        if not ev.criteria_results:
            lines.append("- 評価軸の詳細: なし")
            lines.append("")
            continue

        lines.append("| 評価軸 | 判定 | スコア | 所見 | 根拠 |")
        lines.append("|------|------|------|------|------|")
        for r in ev.criteria_results:
            evidence = _format_evidence(r.evidence)
            score = str(r.score) if r.score is not None else "-"
            summary = r.summary or "-"
            lines.append(
                f"| {r.criterion_key.value} | {_verdict_label(r.verdict)} | {score} | {summary} | {evidence} |"
            )
        lines.append("")

    return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class DecisionInput:
    selected: List[ApiCandidate]
    rejected: List[ApiCandidate]
    selected_reasons: List[str]
    rejected_reasons: List[str]
    prerequisites: List[str]
    disclosure_notes: List[str] = field(default_factory=list)


def render_decision_record_markdown(decision: DecisionInput, *, decided_at: date) -> str:
    """Generate a DecisionRecord markdown.

    Preconditions/prerequisites must not include any secret values.
    """

    lines: List[str] = []
    lines.append("# DecisionRecord")
    lines.append("")
    lines.append(f"- decided_at: {decided_at.isoformat()}")
    lines.append("")

    lines.append("## 採用")
    if decision.selected:
        for c in decision.selected:
            lines.append(f"- {c.provider} / {c.name}")
    else:
        lines.append("- （未決定）")
    lines.append("")

    lines.append("## 採用理由")
    if decision.selected_reasons:
        for r in decision.selected_reasons:
            lines.append(f"- {r}")
    else:
        lines.append("- （未記録）")
    lines.append("")

    lines.append("## 不採用")
    if decision.rejected:
        for c in decision.rejected:
            lines.append(f"- {c.provider} / {c.name}")
    else:
        lines.append("- （なし）")
    lines.append("")

    lines.append("## 不採用理由")
    if decision.rejected_reasons:
        for r in decision.rejected_reasons:
            lines.append(f"- {r}")
    else:
        lines.append("- （未記録）")
    lines.append("")

    lines.append("## 導入前提（機密は含めない）")
    if decision.prerequisites:
        for p in decision.prerequisites:
            lines.append(f"- {p}")
    else:
        lines.append("- （未記録）")
    lines.append("")

    lines.append("## UI/説明で明示すべき事項")
    if decision.disclosure_notes:
        for n in decision.disclosure_notes:
            lines.append(f"- {n}")
    else:
        lines.append("- （未記録）")
    lines.append("")

    return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class RiskItem:
    title: str
    impact: str
    mitigation: str
    evidence: Optional[EvidenceRef] = None


def render_risk_register_markdown(risks: List[RiskItem], *, created_at: date) -> str:
    lines: List[str] = []
    lines.append("# RiskRegister")
    lines.append("")
    lines.append(f"- created_at: {created_at.isoformat()}")
    lines.append("")
    lines.append("| リスク | 影響 | 対策 | 根拠 |")
    lines.append("|------|------|------|------|")
    for r in risks:
        lines.append(f"| {r.title} | {r.impact} | {r.mitigation} | {_format_evidence(r.evidence)} |")
    lines.append("")
    return "\n".join(lines) + "\n"

