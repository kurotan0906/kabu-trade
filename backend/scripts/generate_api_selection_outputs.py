"""
Generate api-selection outputs into `.kiro/specs/api-selection/outputs/`.

Notes:
- This script uses non-secret schemas only.
- It intentionally does NOT read or print any secret values.
- For now, it generates a baseline example using the same candidate examples as the
  earlier on-screen run. Replace the candidate construction section with your
  real collected candidate data when ready.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

# Ensure `backend/` is on sys.path so `import app...` works when executed from repo root.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.schemas.api_selection import (
    AccessTier,
    ApiCandidate,
    AuthMethod,
    FreshnessSummary,
    EvidenceRef,
    MarketCoverage,
    MarketScope,
    PricingSummary,
    TermsSummary,
    Verdict,
)
from app.services.api_selection_reports import (
    DecisionInput,
    RiskItem,
    render_candidate_matrix_markdown,
    render_decision_record_markdown,
    render_risk_register_markdown,
)
from app.services.api_selection_service import EvaluationCriteriaSet, build_candidate_evaluation


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    out_dir = repo_root / ".kiro" / "specs" / "api-selection" / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    checked_at = date.today()

    # --- Candidate examples (non-secret). Replace with your own candidate list. ---
    twelve_data = ApiCandidate(
        provider="Twelve Data",
        name="Tokyo Stock Exchange (XJPX)",
        auth_method=AuthMethod.API_KEY,
        homepage_url="https://twelvedata.com/exchanges/XJPX",
        # Coverage of "Prime" as a concept is not explicit here → leave to HOLD by omitting market_coverage.
        pricing=PricingSummary(
            access_tier=AccessTier.PAID,
            summary="JPX（XJPX）は Pro+ プラン対象として掲載（無料開始は不可の可能性）",
            evidence=EvidenceRef(
                source_name="Twelve Data XJPX page",
                url="https://twelvedata.com/exchanges/XJPX",
                checked_at=checked_at,
            ),
        ),
        terms=TermsSummary(
            redistribution_allowed=None,
            summary="再配布可否は要確認（利用規約を一次情報で確認）",
            evidence=EvidenceRef(
                source_name="Twelve Data XJPX page",
                url="https://twelvedata.com/exchanges/XJPX",
                checked_at=checked_at,
            ),
        ),
        freshness=FreshnessSummary(
            max_delay_days=None,
            recent_data_gap_days=None,
            summary="XJPX の Delay 表記は「–」（遅延の明記がないため要確認）",
            evidence=EvidenceRef(
                source_name="Twelve Data XJPX page",
                url="https://twelvedata.com/exchanges/XJPX",
                checked_at=checked_at,
            ),
        ),
    )

    rapidapi_yahoo = ApiCandidate(
        provider="RapidAPI",
        name="Yahu Financials (Yahoo Finance API on RapidAPI)",
        auth_method=AuthMethod.API_KEY,
        homepage_url="https://rapidapi.com/apidojo/api/yahoo-finance1/pricing",
        pricing=PricingSummary(
            access_tier=AccessTier.FREE,
            summary="Free plan あり（500 req/月、5 rps）。ただしデータの鮮度/提供範囲/規約は要確認",
            evidence=EvidenceRef(
                source_name="RapidAPI pricing",
                url="https://rapidapi.com/apidojo/api/yahoo-finance1/pricing",
                checked_at=checked_at,
            ),
        ),
        terms=TermsSummary(
            redistribution_allowed=None,
            summary="提供元（Yahoo等）の規約・再配布条件が不明なため要確認",
            evidence=EvidenceRef(
                source_name="RapidAPI pricing",
                url="https://rapidapi.com/apidojo/api/yahoo-finance1/pricing",
                checked_at=checked_at,
            ),
        ),
        freshness=FreshnessSummary(
            max_delay_days=None,
            recent_data_gap_days=None,
            summary="データ鮮度（遅延/直近欠落）は要確認",
            evidence=EvidenceRef(
                source_name="RapidAPI pricing",
                url="https://rapidapi.com/apidojo/api/yahoo-finance1/pricing",
                checked_at=checked_at,
            ),
        ),
    )

    kabu_station = ApiCandidate(
        provider="三菱UFJ eスマート証券",
        name="kabuステーションAPI",
        auth_method=AuthMethod.SESSION_TOKEN,
        homepage_url="https://kabu.com/item/kabustation_api/default.html",
        market_coverage=MarketCoverage(
            scope=MarketScope.JPX_ALL,
            supports_required_scope=True,
            evidence=EvidenceRef(
                source_name="kabuステーションAPIリファレンス（市場区分）",
                url="https://kabucom.github.io/kabusapi/reference/index.html",
                checked_at=checked_at,
            ),
        ),
        pricing=PricingSummary(
            access_tier=AccessTier.FREE,
            summary="kabuステーション Professional プラン以上で無料利用（事前設定が必要）",
            evidence=EvidenceRef(
                source_name="kabuステーションAPI（利用料金/無料条件）",
                url="https://kabu.com/item/kabustation_api/default.html",
                checked_at=checked_at,
            ),
        ),
        terms=TermsSummary(
            redistribution_allowed=None,
            summary="利用規約（再配布可否等）は要確認（ポータルの Terms of Service を参照）",
            evidence=EvidenceRef(
                source_name="kabuステーションAPIリファレンス",
                url="https://kabucom.github.io/kabusapi/reference/index.html",
                checked_at=checked_at,
            ),
        ),
        freshness=FreshnessSummary(
            max_delay_days=0,
            recent_data_gap_days=None,
            summary="時価情報・板情報 API あり（ローカル常駐/トークン/レート制限の制約あり）",
            evidence=EvidenceRef(
                source_name="kabuステーションAPIリファレンス（時価情報・板情報）",
                url="https://kabucom.github.io/kabusapi/reference/index.html",
                checked_at=checked_at,
            ),
        ),
    )

    criteria_set = EvaluationCriteriaSet()
    evaluations = [
        build_candidate_evaluation(
            candidate=twelve_data,
            criteria_set=criteria_set,
            required_market_scope=MarketScope.JPX_PRIME,
            checked_at=checked_at,
        ),
        build_candidate_evaluation(
            candidate=rapidapi_yahoo,
            criteria_set=criteria_set,
            required_market_scope=MarketScope.JPX_PRIME,
            checked_at=checked_at,
        ),
        build_candidate_evaluation(
            candidate=kabu_station,
            criteria_set=criteria_set,
            required_market_scope=MarketScope.JPX_PRIME,
            checked_at=checked_at,
        ),
    ]
    (out_dir / "candidate-matrix.md").write_text(render_candidate_matrix_markdown(evaluations), encoding="utf-8")

    selected = [ev.candidate for ev in evaluations if ev.gate_verdict == Verdict.PASS]
    rejected = [ev.candidate for ev in evaluations if ev.gate_verdict != Verdict.PASS]
    disclosure_notes = []
    for ev in evaluations:
        disclosure_notes.extend(ev.disclosure_notes)

    decision = DecisionInput(
        selected=selected,
        rejected=rejected,
        selected_reasons=[
            "ゲート条件（プライム市場対応/無料開始/鮮度）を満たす候補を採用する"
        ]
        if selected
        else ["（未決定）ゲート条件を満たす候補がない/根拠不足のため保留"],
        rejected_reasons=[
            "ゲート条件を満たさない、または根拠不足のため保留/不採用"
        ]
        if rejected
        else [],
        prerequisites=[
            "JQUANTS_ID_TOKEN を設定する（値は記録しない）",
            "鮮度（遅延/直近欠落）と呼び出し制限が要件に許容範囲か一次情報で確認する",
        ],
        disclosure_notes=sorted(set(disclosure_notes)),
    )
    (out_dir / "decision-record.md").write_text(
        render_decision_record_markdown(decision, decided_at=checked_at),
        encoding="utf-8",
    )

    risks = [
        RiskItem(
            title="無料/利用条件の変更",
            impact="無料利用条件やプランが変わりPoCや運用に影響",
            mitigation="一次情報を定期再確認し、代替候補を保持",
            evidence=kabu_station.pricing.evidence,
        ),
        RiskItem(
            title="直近データ欠落/遅延（鮮度不足）",
            impact="評価/チャート/直近シグナルが破綻する可能性",
            mitigation="鮮度を一次情報で確認し、満たせない場合はフォールバック構成（別API併用/有償移行）を必須化",
            evidence=twelve_data.freshness.evidence if twelve_data.freshness else None,
        ),
        RiskItem(
            title="利用規約/再配布条件の不確実性",
            impact="キャッシュ/表示/共有の運用が制約される可能性",
            mitigation="再配布可否を一次情報で確認し、運用設計を合わせる",
            evidence=rapidapi_yahoo.terms.evidence,
        ),
    ]
    (out_dir / "risk-register.md").write_text(
        render_risk_register_markdown(risks, created_at=checked_at),
        encoding="utf-8",
    )

    print(f"✅ Written outputs to: {out_dir}")
    print("- candidate-matrix.md")
    print("- decision-record.md")
    print("- risk-register.md")


if __name__ == "__main__":
    main()

