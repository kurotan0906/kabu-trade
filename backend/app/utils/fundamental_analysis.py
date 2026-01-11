"""Fundamental analysis utilities"""

from typing import Optional, Dict, Any
from decimal import Decimal
from app.schemas.stock import StockInfo


class FundamentalAnalysis:
    """ファンダメンタル分析クラス"""

    @staticmethod
    def evaluate_per(per: Optional[Decimal]) -> Dict[str, Any]:
        """
        PERを評価
        
        Args:
            per: PER値
            
        Returns:
            Dict[str, Any]: 評価結果（スコア、評価、説明）
        """
        if per is None:
            return {
                "score": 50,  # 中立
                "evaluation": "不明",
                "description": "PERデータがありません",
            }

        per_value = float(per)

        if per_value < 10:
            return {
                "score": 80,
                "evaluation": "割安",
                "description": f"PER {per_value:.2f}は割安水準です",
            }
        elif per_value < 15:
            return {
                "score": 60,
                "evaluation": "適正",
                "description": f"PER {per_value:.2f}は適正水準です",
            }
        elif per_value < 25:
            return {
                "score": 40,
                "evaluation": "やや高値",
                "description": f"PER {per_value:.2f}はやや高値水準です",
            }
        else:
            return {
                "score": 20,
                "evaluation": "高値",
                "description": f"PER {per_value:.2f}は高値水準です",
            }

    @staticmethod
    def evaluate_pbr(pbr: Optional[Decimal]) -> Dict[str, Any]:
        """
        PBRを評価
        
        Args:
            pbr: PBR値
            
        Returns:
            Dict[str, Any]: 評価結果（スコア、評価、説明）
        """
        if pbr is None:
            return {
                "score": 50,  # 中立
                "evaluation": "不明",
                "description": "PBRデータがありません",
            }

        pbr_value = float(pbr)

        if pbr_value < 0.8:
            return {
                "score": 80,
                "evaluation": "割安",
                "description": f"PBR {pbr_value:.2f}は割安水準です（1倍割れ）",
            }
        elif pbr_value < 1.2:
            return {
                "score": 60,
                "evaluation": "適正",
                "description": f"PBR {pbr_value:.2f}は適正水準です",
            }
        elif pbr_value < 2.0:
            return {
                "score": 40,
                "evaluation": "やや高値",
                "description": f"PBR {pbr_value:.2f}はやや高値水準です",
            }
        else:
            return {
                "score": 20,
                "evaluation": "高値",
                "description": f"PBR {pbr_value:.2f}は高値水準です",
            }

    @staticmethod
    def evaluate_financial_health(stock_info: StockInfo) -> Dict[str, Any]:
        """
        財務健全性を評価
        
        Args:
            stock_info: 銘柄情報
            
        Returns:
            Dict[str, Any]: 評価結果
        """
        scores = []
        descriptions = []

        # PER評価
        per_eval = FundamentalAnalysis.evaluate_per(stock_info.per)
        scores.append(per_eval["score"])
        descriptions.append(per_eval["description"])

        # PBR評価
        pbr_eval = FundamentalAnalysis.evaluate_pbr(stock_info.pbr)
        scores.append(pbr_eval["score"])
        descriptions.append(pbr_eval["description"])

        # 平均スコアを計算
        avg_score = sum(scores) / len(scores) if scores else 50

        if avg_score >= 70:
            evaluation = "良好"
        elif avg_score >= 50:
            evaluation = "普通"
        else:
            evaluation = "注意"

        return {
            "score": int(avg_score),
            "evaluation": evaluation,
            "per_evaluation": per_eval,
            "pbr_evaluation": pbr_eval,
            "descriptions": descriptions,
        }
