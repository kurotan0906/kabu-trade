"""Maintenance helpers for API selection artifacts.

Implements:
- Evidence link re-checking (5.1)
- Update history tracking (5.2)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
from typing import Iterable, List, Optional

import httpx

from app.schemas.api_selection import EvidenceRef, FreshnessSummary, GatePolicy


class EvidenceStatus(str, Enum):
    OK = "ok"
    UNREACHABLE = "unreachable"
    ERROR = "error"
    MISSING_URL = "missing_url"
    STALE = "stale"


@dataclass(frozen=True)
class EvidenceCheckResult:
    evidence: EvidenceRef
    status: EvidenceStatus
    message: Optional[str] = None


async def check_evidence_link(
    evidence: EvidenceRef,
    *,
    timeout_seconds: float = 10.0,
) -> EvidenceCheckResult:
    """Re-check a single evidence URL.

    If URL is missing, returns MISSING_URL.
    If request fails, returns UNREACHABLE/ERROR.
    """

    if not evidence.url:
        return EvidenceCheckResult(evidence=evidence, status=EvidenceStatus.MISSING_URL)

    async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
        try:
            r = await client.head(str(evidence.url))
            if r.status_code >= 400:
                # Some sites disallow HEAD; fall back to GET.
                r = await client.get(str(evidence.url))
            if r.status_code >= 400:
                return EvidenceCheckResult(
                    evidence=evidence,
                    status=EvidenceStatus.ERROR,
                    message=f"HTTP {r.status_code}",
                )
            return EvidenceCheckResult(evidence=evidence, status=EvidenceStatus.OK)
        except httpx.TimeoutException:
            return EvidenceCheckResult(
                evidence=evidence,
                status=EvidenceStatus.UNREACHABLE,
                message="timeout",
            )
        except httpx.RequestError as e:
            return EvidenceCheckResult(
                evidence=evidence,
                status=EvidenceStatus.UNREACHABLE,
                message=str(e),
            )
        except Exception as e:
            return EvidenceCheckResult(
                evidence=evidence,
                status=EvidenceStatus.ERROR,
                message=str(e),
            )


def detect_stale_evidence(
    evidences: Iterable[EvidenceRef],
    *,
    today: date,
    stale_after_days: int = 90,
) -> List[EvidenceCheckResult]:
    """Detect stale evidence by checked_at age."""

    threshold = today - timedelta(days=stale_after_days)
    results: List[EvidenceCheckResult] = []
    for e in evidences:
        if e.checked_at < threshold:
            results.append(
                EvidenceCheckResult(
                    evidence=e,
                    status=EvidenceStatus.STALE,
                    message=f"checked_at={e.checked_at.isoformat()} (< {threshold.isoformat()})",
                )
            )
    return results


@dataclass(frozen=True)
class UpdateHistoryEntry:
    updated_at: date
    change_summary: str
    impact_summary: str


def append_update_history(
    history: List[UpdateHistoryEntry],
    entry: UpdateHistoryEntry,
) -> List[UpdateHistoryEntry]:
    """Append an entry keeping reverse-chronological order."""

    new_history = [entry] + [h for h in history if h != entry]
    return sorted(new_history, key=lambda x: x.updated_at, reverse=True)


@dataclass(frozen=True)
class FatalReevaluationTrigger:
    required: bool
    message: Optional[str] = None


def should_trigger_fatal_reevaluation(
    *,
    previous: Optional[FreshnessSummary],
    current: Optional[FreshnessSummary],
    gate: GatePolicy,
) -> FatalReevaluationTrigger:
    """Decide whether a fatal-condition (freshness) re-evaluation is required (5.3).

    This is a lightweight policy helper intended for automation hooks.
    """

    if previous is None or current is None:
        return FatalReevaluationTrigger(required=True, message="鮮度情報が未記録のため再評価が必要です")

    if (
        previous.max_delay_days != current.max_delay_days
        or previous.recent_data_gap_days != current.recent_data_gap_days
    ):
        return FatalReevaluationTrigger(required=True, message="鮮度/欠落の仕様が変更されたため再評価が必要です")

    if current.max_delay_days is None:
        return FatalReevaluationTrigger(required=True, message="鮮度の根拠が不明になったため再評価が必要です")

    if current.max_delay_days > gate.max_delay_days:
        return FatalReevaluationTrigger(
            required=True,
            message=f"鮮度が致命条件を満たしません（遅延={current.max_delay_days}日 > 許容={gate.max_delay_days}日）",
        )

    return FatalReevaluationTrigger(required=False)

