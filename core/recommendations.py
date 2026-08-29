from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List

from .domain import Recommendation
from .statistics_service import StatisticsService
from .ml import RiskPredictionService


@dataclass
class RecommendationEngine:
    """Rule-based engine that looks at live statistics and ML risk scores and generates actionable Recommendation objects."""
    statistics_service: StatisticsService
    risk_service: RiskPredictionService

    def generate(self, filters: Dict[str, Any]) -> List[Recommendation]:
        recs: List[Recommendation] = []

        stats = self.statistics_service.get_statistics(filters)
        overall_rate = float(stats.get("overall_return_rate") or 0.0)

        if overall_rate >= 0.4:
            recs.append(
                Recommendation(
                    title="High overall return rate detected",
                    description="Overall return rate is high. Review top return reasons and high-risk products to target interventions.",
                    priority="High",
                )
            )

        high_risk = self.risk_service.get_high_risk_products(top_n=5, filters=filters)
        if high_risk:
            top = high_risk[0]
            recs.append(
                Recommendation(
                    title="Top high-risk product identified",
                    description=f"Product {top['product_id']} has the highest average risk score. Consider checking sizing/quality info and return reasons for this item.",
                    priority="Medium",
                )
            )

        return recs
