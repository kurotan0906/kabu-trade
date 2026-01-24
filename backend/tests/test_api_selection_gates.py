from datetime import date

from app.schemas.api_selection import (
    AccessTier,
    ApiCandidate,
    AuthMethod,
    FreshnessSummary,
    EvaluationCriteriaSet,
    GatePolicy,
    MarketCoverage,
    MarketScope,
    PricingSummary,
    Verdict,
)
from app.services.api_selection_service import build_candidate_evaluation, evaluate_gate


def test_gate_holds_when_missing_required_fields():
    candidate = ApiCandidate(provider="X", name="Y", auth_method=AuthMethod.NONE)
    verdict, reasons = evaluate_gate(
        candidate=candidate,
        required_market_scope=MarketScope.JPX_PRIME,
        gate=GatePolicy(require_prime_market=True, require_free_start=True),
    )
    assert verdict == Verdict.HOLD
    assert reasons


def test_gate_passes_when_prime_and_free_requirements_met():
    candidate = ApiCandidate(
        provider="JPX",
        name="J-Quants API",
        auth_method=AuthMethod.API_KEY,
        market_coverage=MarketCoverage(scope=MarketScope.JPX_ALL, supports_required_scope=True),
        pricing=PricingSummary(access_tier=AccessTier.FREE),
        freshness=FreshnessSummary(max_delay_days=1),
    )
    verdict, reasons = evaluate_gate(
        candidate=candidate,
        required_market_scope=MarketScope.JPX_PRIME,
        gate=GatePolicy(require_prime_market=True, require_free_start=True),
    )
    assert verdict == Verdict.PASS
    assert reasons == []


def test_gate_fails_when_free_requirement_not_met():
    candidate = ApiCandidate(
        provider="Vendor",
        name="Paid API",
        auth_method=AuthMethod.API_KEY,
        market_coverage=MarketCoverage(scope=MarketScope.JPX_ALL, supports_required_scope=True),
        pricing=PricingSummary(access_tier=AccessTier.PAID),
        freshness=FreshnessSummary(max_delay_days=1),
    )
    verdict, reasons = evaluate_gate(
        candidate=candidate,
        required_market_scope=MarketScope.JPX_PRIME,
        gate=GatePolicy(require_prime_market=True, require_free_start=True),
    )
    assert verdict == Verdict.FAIL
    assert reasons


def test_gate_fails_when_prime_requirement_not_met():
    candidate = ApiCandidate(
        provider="Vendor",
        name="No Prime",
        auth_method=AuthMethod.API_KEY,
        market_coverage=MarketCoverage(scope=MarketScope.JPX_ALL, supports_required_scope=False),
        pricing=PricingSummary(access_tier=AccessTier.FREE),
        freshness=FreshnessSummary(max_delay_days=1),
    )
    verdict, reasons = evaluate_gate(
        candidate=candidate,
        required_market_scope=MarketScope.JPX_PRIME,
        gate=GatePolicy(require_prime_market=True, require_free_start=True),
    )
    assert verdict in (Verdict.FAIL, Verdict.HOLD)
    assert reasons


def test_gate_holds_when_freshness_fails_but_free_start_is_met_requires_fallback():
    candidate = ApiCandidate(
        provider="JPX",
        name="Free but stale",
        auth_method=AuthMethod.API_KEY,
        market_coverage=MarketCoverage(scope=MarketScope.JPX_ALL, supports_required_scope=True),
        pricing=PricingSummary(access_tier=AccessTier.FREE),
        freshness=FreshnessSummary(max_delay_days=30),
    )
    verdict, reasons = evaluate_gate(
        candidate=candidate,
        required_market_scope=MarketScope.JPX_PRIME,
        gate=GatePolicy(require_prime_market=True, require_free_start=True, require_fresh_data=True, max_delay_days=5),
    )
    assert verdict == Verdict.HOLD
    assert any("鮮度要件" in r for r in reasons)
    assert any("フォールバック案" in r for r in reasons)


def test_build_candidate_evaluation_outputs_gate_and_reasons():
    candidate = ApiCandidate(provider="JPX", name="J-Quants API", auth_method=AuthMethod.API_KEY)
    ev = build_candidate_evaluation(
        candidate=candidate,
        criteria_set=EvaluationCriteriaSet(),
        required_market_scope=MarketScope.JPX_PRIME,
        checked_at=date(2026, 1, 1),
    )
    assert ev.checked_at == date(2026, 1, 1)
    assert ev.gate_verdict in (Verdict.HOLD, Verdict.FAIL, Verdict.PASS)

