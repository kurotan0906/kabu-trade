"""phase_scorer のユニットテスト"""

from app.analyzer.phase_scorer import (
    get_phase,
    get_score_weights,
    apply_phase_weights,
    profile_for_phase,
    score_to_dict,
)
from app.analyzer.scoring_profiles import GROWTH_PROFILE, BALANCED_PROFILE, INCOME_PROFILE


class TestGetPhase:
    def test_accumulation(self):
        assert get_phase(0) == "積立期"
        assert get_phase(29.9) == "積立期"

    def test_growth(self):
        assert get_phase(30) == "成長期"
        assert get_phase(50) == "成長期"
        assert get_phase(69.9) == "成長期"

    def test_stable(self):
        assert get_phase(70) == "安定期"
        assert get_phase(150) == "安定期"


class TestProfileForPhase:
    def test_mapping(self):
        assert profile_for_phase("積立期") is GROWTH_PROFILE
        assert profile_for_phase("成長期") is BALANCED_PROFILE
        assert profile_for_phase("安定期") is INCOME_PROFILE


class TestApplyPhaseWeights:
    def test_accumulation_bonus(self):
        weights = get_score_weights("積立期")
        score = {
            "total_score": 60,
            "revenue_growth": 0.3,
            "roe": 0.2,
            "dividend_yield": 0.01,
            "pbr": 1.1,
            "technical_score": 40,
        }
        result = apply_phase_weights(score, weights)
        # 積立期: +3 (growth) +2 (roe) -2 (div) +0 (pbr) +2 (tech) = +5
        assert result["adjusted_total_score"] == 65

    def test_stable_bonus(self):
        weights = get_score_weights("安定期")
        score = {
            "total_score": 50,
            "revenue_growth": 0.05,
            "roe": 0.12,
            "dividend_yield": 0.04,
            "pbr": 1.0,
            "technical_score": 30,
        }
        result = apply_phase_weights(score, weights)
        # 安定期: -2 +0 +3 +2 -1 = +2
        assert result["adjusted_total_score"] == 52

    def test_none_fields_skip_bonus(self):
        weights = get_score_weights("積立期")
        score = {
            "total_score": 50,
            "revenue_growth": None,
            "roe": None,
            "dividend_yield": None,
            "pbr": None,
            "technical_score": None,
        }
        result = apply_phase_weights(score, weights)
        assert result["adjusted_total_score"] == 50  # ボーナスなし

    def test_clamp_upper(self):
        weights = get_score_weights("安定期")
        score = {
            "total_score": 99,
            "revenue_growth": 0.05,
            "roe": 0.12,
            "dividend_yield": 0.04,
            "pbr": 1.0,
            "technical_score": 30,
        }
        result = apply_phase_weights(score, weights)
        assert result["adjusted_total_score"] == 100

    def test_clamp_lower(self):
        weights = get_score_weights("安定期")
        score = {
            "total_score": 0,
            "revenue_growth": 0.05,
            "roe": None,
            "dividend_yield": None,
            "pbr": None,
            "technical_score": 30,
        }
        # 安定期: revenue=-2 + tech=-1 = -3 → clamp to 0
        result = apply_phase_weights(score, weights)
        assert result["adjusted_total_score"] == 0


class TestScoreToDict:
    def test_from_orm_like(self):
        class _Fake:
            total_score = 70
            revenue_growth = 0.1
            roe = 0.15
            dividend_yield = 0.03
            pbr = 1.2
            technical_score = 35
        d = score_to_dict(_Fake())
        assert d["total_score"] == 70
        assert d["roe"] == 0.15
