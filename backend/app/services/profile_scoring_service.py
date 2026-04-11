"""プロファイル別スコア再計算サービス

DB から取得した StockScore を任意のプロファイルで再ランク付けする。
Phase 4 の phase_scorer（ライフステージボーナス）もここから呼ばれる。
"""

from typing import List, Literal, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.analyzer.scoring_profiles import (
    ScoringProfile,
    compute_phase_score,
    get_profile,
)
from app.models.stock_score import StockScore


ProfileKey = Literal["growth", "balanced", "income", "auto"]


async def list_scores_with_profile(
    db: AsyncSession,
    profile_key: str,
    limit: int = 100,
    progress_rate: Optional[float] = None,
) -> list[dict]:
    """最新スコアを取得し、プロファイル適用後の phase_score で並べ直す。

    profile_key="auto" のときは phase_scorer から進捗率に応じたプロファイルを選択する。
    返り値は StockScore ORM + profile_score/profile_name/current_phase/adjusted_total_score
    を載せた dict のリスト。
    """
    subq = (
        select(StockScore.symbol, func.max(StockScore.scored_at).label("latest"))
        .group_by(StockScore.symbol)
        .subquery()
    )
    stmt = (
        select(StockScore)
        .join(subq, (StockScore.symbol == subq.c.symbol) & (StockScore.scored_at == subq.c.latest))
        .where(StockScore.data_quality != "fetch_error")
    )
    result = await db.execute(stmt)
    scores: List[StockScore] = list(result.scalars().all())

    profile, current_phase = _resolve_profile(profile_key, progress_rate)

    # current_phase が決まっていれば phase_scorer のボーナスも乗せる
    weights = None
    if current_phase is not None:
        from app.analyzer.phase_scorer import get_score_weights, apply_phase_weights, score_to_dict
        weights = get_score_weights(current_phase)

    enriched = []
    for s in scores:
        p_score = compute_phase_score(s, profile)
        adjusted = None
        if weights is not None:
            from app.analyzer.phase_scorer import apply_phase_weights, score_to_dict
            adjusted_dict = apply_phase_weights(score_to_dict(s), weights)
            adjusted = adjusted_dict.get("adjusted_total_score")
        enriched.append({
            "score": s,
            "profile_score": p_score,
            "profile_name": profile.name,
            "current_phase": current_phase,
            "adjusted_total_score": adjusted,
        })

    # auto モードでは adjusted_total_score 優先、それ以外は profile_score でソート
    def _sort_key(item):
        if item["adjusted_total_score"] is not None:
            return item["adjusted_total_score"]
        return item["profile_score"] or 0

    enriched.sort(key=_sort_key, reverse=True)
    return enriched[:limit]


def _resolve_profile(profile_key: str, progress_rate: Optional[float]) -> tuple[ScoringProfile, Optional[str]]:
    """profile_key と進捗率から (ScoringProfile, current_phase) を決める。

    - auto: progress_rate から phase 判定 → 積立期=growth, 成長期=balanced, 安定期=income
    - それ以外: 指定プロファイルをそのまま返す（current_phase=None）
    """
    if profile_key == "auto":
        from app.analyzer.phase_scorer import get_phase, profile_for_phase
        phase = get_phase(progress_rate or 0.0)
        return profile_for_phase(phase), phase
    return get_profile(profile_key), None
