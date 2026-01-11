"""Evaluation service - 評価サービス"""

from typing import Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.stock_repository import StockRepository
from app.services.stock_service import StockService
from app.services.analysis_engine import AnalysisEngine
from app.models.evaluation import Evaluation
from app.schemas.evaluation import EvaluationResult
from app.core.exceptions import StockNotFoundError


class EvaluationService:
    """Evaluation service - 評価サービス"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.stock_service = StockService(db)
        self.analysis_engine = AnalysisEngine()

    async def evaluate_stock(
        self, code: str, period: str = "1y"
    ) -> EvaluationResult:
        """
        銘柄を評価
        
        Args:
            code: 銘柄コード
            period: 評価期間（デフォルト: 1y）
            
        Returns:
            EvaluationResult: 評価結果
        """
        # 銘柄情報を取得
        stock_info = await self.stock_service.get_stock_info(code)
        if not stock_info:
            raise StockNotFoundError(code)

        # 株価データを取得
        prices = await self.stock_service.get_stock_prices(code, period=period)
        if not prices:
            raise StockNotFoundError(f"{code}の株価データが見つかりません")

        # テクニカル分析
        technical = self.analysis_engine.calculate_technical_indicators(prices)

        # ファンダメンタル分析
        fundamental = self.analysis_engine.calculate_fundamental_metrics(stock_info)

        # 現在の株価を取得
        current_price = stock_info.current_price or prices[-1].close

        # 買い時・売り時判定
        buy_signal = self.analysis_engine.determine_buy_signal(
            technical, fundamental, current_price
        )
        sell_signal = self.analysis_engine.determine_sell_signal(
            technical, fundamental, current_price
        )

        # 推奨アクションを決定
        if buy_signal["score"] >= 60 and sell_signal["score"] < 40:
            recommendation = "買い"
        elif sell_signal["score"] >= 60 and buy_signal["score"] < 40:
            recommendation = "売り"
        elif buy_signal["score"] >= 50:
            recommendation = "保持"
        else:
            recommendation = "様子見"

        # 評価結果を作成
        evaluation_result = EvaluationResult(
            stock_code=code,
            stock_name=stock_info.name,
            buy_score=buy_signal["score"],
            sell_score=sell_signal["score"],
            buy_recommendation=buy_signal["recommendation"],
            sell_recommendation=sell_signal["recommendation"],
            technical_indicators=self._convert_technical_to_response(technical),
            fundamental_metrics=self._convert_fundamental_to_response(fundamental),
            buy_signal=self._convert_signal_to_response(buy_signal, "buy"),
            sell_signal=self._convert_signal_to_response(sell_signal, "sell"),
            evaluation_date=datetime.now(),
        )

        # データベースに保存
        await self._save_evaluation(evaluation_result)

        return evaluation_result

    def _convert_technical_to_response(self, technical: dict):
        """テクニカル指標をレスポンス形式に変換"""
        from app.schemas.evaluation import TechnicalIndicatorsResponse
        
        def convert_value(v):
            """値をfloatに変換"""
            if isinstance(v, Decimal):
                return float(v)
            return v
        
        return TechnicalIndicatorsResponse(
            moving_averages={
                k: convert_value(v)
                for k, v in technical.get("moving_averages", {}).items()
            },
            rsi=convert_value(technical.get("rsi", Decimal("50"))),
            macd={
                k: convert_value(v)
                for k, v in technical.get("macd", {}).items()
            },
            bollinger_bands={
                k: convert_value(v)
                for k, v in technical.get("bollinger_bands", {}).items()
            },
            support_resistance={
                k: convert_value(v)
                for k, v in technical.get("support_resistance", {}).items()
            },
        )

    def _convert_fundamental_to_response(self, fundamental: dict):
        """ファンダメンタル指標をレスポンス形式に変換"""
        from app.schemas.evaluation import FundamentalMetricsResponse
        
        return FundamentalMetricsResponse(
            score=fundamental.get("score", 50),
            evaluation=fundamental.get("evaluation", "不明"),
            per_evaluation=fundamental.get("per_evaluation", {}),
            pbr_evaluation=fundamental.get("pbr_evaluation", {}),
            descriptions=fundamental.get("descriptions", []),
        )

    def _convert_signal_to_response(self, signal: dict, signal_type: str = "buy"):
        """シグナルをレスポンス形式に変換"""
        from app.schemas.evaluation import BuySignalResponse, SellSignalResponse
        
        if signal_type == "buy":
            return BuySignalResponse(
                score=signal.get("score", 50),
                recommendation=signal.get("recommendation", "不明"),
                reasons=signal.get("reasons", []),
            )
        else:
            return SellSignalResponse(
                score=signal.get("score", 50),
                recommendation=signal.get("recommendation", "不明"),
                reasons=signal.get("reasons", []),
            )

    async def _save_evaluation(self, evaluation_result: EvaluationResult):
        """評価結果をデータベースに保存"""
        evaluation = Evaluation(
            stock_code=evaluation_result.stock_code,
            strategy_id=None,  # Phase 3で実装
            buy_score=evaluation_result.buy_score,
            sell_score=evaluation_result.sell_score,
            match_score=None,  # Phase 3で実装
            recommendation=evaluation_result.buy_recommendation,  # 簡易実装
            evaluation_date=evaluation_result.evaluation_date,
            details={
                "technical_indicators": evaluation_result.technical_indicators.model_dump(),
                "fundamental_metrics": evaluation_result.fundamental_metrics.model_dump(),
                "buy_signal": evaluation_result.buy_signal.model_dump(),
                "sell_signal": evaluation_result.sell_signal.model_dump(),
            },
        )

        self.db.add(evaluation)
        await self.db.commit()
        await self.db.refresh(evaluation)

        evaluation_result.id = evaluation.id
