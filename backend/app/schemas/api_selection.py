"""API selection schemas (non-secret)"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class FreshnessSummary(BaseModel):
    """データ鮮度の要約（直近欠落や遅延の表現）"""

    max_delay_days: Optional[int] = Field(
        None,
        ge=0,
        description="最新データの遅延日数（例: 0=当日、1=1営業日遅延の目安。根拠がない場合はNone）",
    )
    recent_data_gap_days: Optional[int] = Field(
        None,
        ge=0,
        description="直近データの欠落がある場合の欠落日数（例: 84=約12週間）。不明/該当なしはNone",
    )
    summary: Optional[str] = Field(None, description="鮮度に関する要点（例: 無料枠は遅延あり）")
    evidence: Optional["EvidenceRef"] = Field(None, description="参照根拠")


class CorporateActionsSummary(BaseModel):
    """コーポレートアクション（分割/併合/配当等）と調整の扱いの要約"""

    adjusted_prices_available: Optional[bool] = Field(
        None, description="調整済み価格（分割/併合等）を提供するか"
    )
    corporate_actions_feed_available: Optional[bool] = Field(
        None, description="コーポレートアクション情報（イベント）を提供するか"
    )
    summary: Optional[str] = Field(None, description="調整・アクションの要点（例: 調整済み/未調整の両方提供）")
    evidence: Optional["EvidenceRef"] = Field(None, description="参照根拠")


class MarketScope(str, Enum):
    """対象市場のスコープ（初期は日本のプライム市場を重視）"""

    JPX_PRIME = "jpx_prime"
    JPX_STANDARD = "jpx_standard"
    JPX_GROWTH = "jpx_growth"
    JPX_ALL = "jpx_all"
    OTHER = "other"


class DataCategory(str, Enum):
    """評価対象となるデータ種別"""

    SYMBOLS = "symbols"
    PRICES_OHLCV = "prices_ohlcv"
    REALTIME_PRICE = "realtime_price"
    FINANCIALS = "financials"
    CORPORATE_ACTIONS = "corporate_actions"
    OTHER = "other"


class UsagePurpose(str, Enum):
    """利用目的"""

    UI_DISPLAY = "ui_display"
    ANALYSIS_INPUT = "analysis_input"
    CACHE_WARMUP = "cache_warmup"
    OTHER = "other"


class AuthMethod(str, Enum):
    """認証方式（機密は保持しない）"""

    NONE = "none"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BASIC = "basic"
    SESSION_TOKEN = "session_token"
    OTHER = "other"


class AccessTier(str, Enum):
    """利用開始のしやすさ（無料開始要件の表現）"""

    FREE = "free"
    FREE_TRIAL = "free_trial"
    PAID = "paid"
    UNKNOWN = "unknown"


class EvidenceRef(BaseModel):
    """根拠参照（一次情報の追跡）"""

    source_name: str = Field(..., description="参照元の名称", example="J-Quants API 仕様")
    url: Optional[HttpUrl] = Field(None, description="参照URL（可能なら）")
    checked_at: date = Field(..., description="確認日")
    note: Optional[str] = Field(None, description="補足メモ（機密は書かない）")


# Resolve forward references for models defined above EvidenceRef.
FreshnessSummary.model_rebuild()
CorporateActionsSummary.model_rebuild()


class MarketCoverage(BaseModel):
    """市場カバレッジ（プライム要件の判定と根拠）"""

    scope: MarketScope = Field(..., description="対象市場スコープ")
    supports_required_scope: bool = Field(
        ..., description="必須市場スコープ（例: JPXプライム）を満たすか"
    )
    evidence: Optional[EvidenceRef] = Field(None, description="判定根拠")


class PricingSummary(BaseModel):
    """料金体系の要点（詳細や最新値は根拠参照に寄せる）"""

    access_tier: AccessTier = Field(..., description="無料/トライアル/有償")
    summary: Optional[str] = Field(None, description="料金の要点（例: 無料枠は遅延あり）")
    evidence: Optional[EvidenceRef] = Field(None, description="参照根拠")


class TermsSummary(BaseModel):
    """利用規約の要点（再配布可否など。機密は含めない）"""

    redistribution_allowed: Optional[bool] = Field(
        None, description="再配布（キャッシュの共有を含む）の可否"
    )
    summary: Optional[str] = Field(None, description="規約の要点（禁止事項など）")
    evidence: Optional[EvidenceRef] = Field(None, description="参照根拠")


class ApiCandidate(BaseModel):
    """外部株式データAPI候補（機密情報は保持しない）"""

    provider: str = Field(..., description="提供元", example="JPX")
    name: str = Field(..., description="API名称", example="J-Quants API")
    homepage_url: Optional[HttpUrl] = Field(None, description="公式ページURL")

    supported_data: List[DataCategory] = Field(
        default_factory=list, description="対応データ種別"
    )
    auth_method: AuthMethod = Field(..., description="認証方式（方式のみ）")

    market_coverage: Optional[MarketCoverage] = Field(
        None, description="市場カバレッジ（プライム要件の判定）"
    )
    pricing: Optional[PricingSummary] = Field(None, description="料金体系の要点")
    terms: Optional[TermsSummary] = Field(None, description="利用規約の要点")
    freshness: Optional[FreshnessSummary] = Field(None, description="データ鮮度（直近欠落/遅延）の要点")
    corporate_actions: Optional[CorporateActionsSummary] = Field(
        None, description="コーポレートアクション/調整の扱いの要点"
    )

    notes: Optional[str] = Field(None, description="補足（機密は書かない）")

    class Config:
        from_attributes = True


class EvaluationScope(BaseModel):
    """選定の評価対象スコープ"""

    market_scope_required: MarketScope = Field(
        MarketScope.JPX_PRIME, description="初期段階の必須市場スコープ"
    )
    data_categories: List[DataCategory] = Field(
        default_factory=list, description="評価対象データ種別"
    )
    purposes: List[UsagePurpose] = Field(
        default_factory=list, description="利用目的"
    )


class CriterionKey(str, Enum):
    """評価軸の識別子（比較表でのキー）"""

    DATA_COVERAGE = "data_coverage"
    LATENCY_FRESHNESS = "latency_freshness"
    AVAILABILITY = "availability"
    AUTH = "auth"
    RATE_LIMITS = "rate_limits"
    COST = "cost"
    TERMS = "terms"
    IMPLEMENTATION_EASE = "implementation_ease"
    OPERATIONS = "operations"
    OTHER = "other"


class CheckMethod(str, Enum):
    """判定方法（確認手段）"""

    DOC_REVIEW = "doc_review"
    SUPPORT_INQUIRY = "support_inquiry"
    API_TEST = "api_test"
    CONTRACT = "contract"
    OTHER = "other"


class Verdict(str, Enum):
    """合否/判定結果"""

    PASS = "pass"
    FAIL = "fail"
    HOLD = "hold"
    UNKNOWN = "unknown"


class CriterionDefinition(BaseModel):
    """評価軸の定義（合否条件と判定方法）"""

    key: CriterionKey = Field(..., description="評価軸キー")
    title: str = Field(..., description="評価軸名（表示用）")
    method: CheckMethod = Field(..., description="確認手段")
    minimum_condition: str = Field(
        ..., description="最低要件（合否条件）。曖昧語を避けて具体化する"
    )
    evidence_required: bool = Field(
        True, description="根拠参照（一次情報）の記録を必須にするか"
    )


class GatePolicy(BaseModel):
    """初期段階のゲート条件（必須要件）"""

    require_prime_market: bool = Field(
        True, description="日本のプライム市場対応を必須とする"
    )
    require_free_start: bool = Field(
        True, description="無料プランまたは無料トライアルでPoC可能であることを必須とする"
    )
    require_fresh_data: bool = Field(True, description="直近データ鮮度の最低要件を必須とする")
    max_delay_days: int = Field(
        5,
        ge=0,
        description="許容する最新データ遅延の最大日数（例: 5=休日・非営業日を含めた許容）",
    )


class EvaluationCriteriaSet(BaseModel):
    """評価基準セット（評価軸 + ゲート条件）"""

    gate: GatePolicy = Field(default_factory=GatePolicy)
    criteria: List[CriterionDefinition] = Field(
        default_factory=list, description="評価軸一覧"
    )


class CriterionEvaluation(BaseModel):
    """候補×評価軸の評価結果"""

    criterion_key: CriterionKey = Field(..., description="評価軸キー")
    verdict: Verdict = Field(..., description="判定結果")
    score: Optional[int] = Field(
        None, ge=0, le=100, description="任意のスコア（0-100）。未使用ならnull"
    )
    summary: Optional[str] = Field(None, description="所見（短文）")
    evidence: Optional[EvidenceRef] = Field(None, description="根拠参照")


class CandidateEvaluation(BaseModel):
    """候補APIの評価（ゲート条件 + 軸ごとの結果 + 根拠）"""

    candidate: ApiCandidate = Field(..., description="評価対象の候補")
    gate_verdict: Verdict = Field(..., description="ゲート条件の最終判定")
    gate_reasons: List[str] = Field(default_factory=list, description="ゲート判定理由")
    criteria_results: List[CriterionEvaluation] = Field(
        default_factory=list, description="評価軸ごとの結果"
    )
    disclosure_notes: List[str] = Field(
        default_factory=list,
        description="UI/説明で明示すべき事項（初心者が誤解しやすい制約など）",
    )
    fallback_plan: Optional[str] = Field(
        None, description="鮮度未達などの場合のフォールバック構成（案）。未作成ならNone"
    )
    checked_at: date = Field(..., description="評価実施日")


