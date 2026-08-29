from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .statistics_service import StatisticsService
from .ml import RiskPredictionService
from .simulation import SimulationService
from .reporting import ReportService
from .recommendations import RecommendationEngine
from .domain import PolicyScenario, SimulationResult, Recommendation


@dataclass
class DashboardController:
    """Top-level facade that wires all services together — app.py only talks to this one object."""
    statistics_service: StatisticsService
    risk_service: RiskPredictionService
    recommendation_engine: RecommendationEngine
    simulation_service: SimulationService
    report_service: ReportService
    active_filters: Dict[str, Any] = field(default_factory=dict)

    def set_filters(self, filters: Dict[str, Any]) -> None:
        self.active_filters = dict(filters or {})

    def get_dashboard_data(self) -> Dict[str, Any]:
        stats   = self.statistics_service.get_statistics(self.active_filters)
        reasons = self.statistics_service.get_return_reason_breakdown(self.active_filters)
        trend   = self.statistics_service.get_return_trend_over_time("monthly", self.active_filters)
        by_cat  = self.statistics_service.get_return_rate_by_field("category", self.active_filters)

        return {
            "statistics":              stats,
            "return_reasons":          reasons,
            "return_trend":            trend,
            "return_rate_by_category": by_cat,
        }

    def get_high_risk_products(self, top_n: int = 10) -> List[Dict[str, Any]]:
        return self.risk_service.get_high_risk_products(top_n, self.active_filters)

    def get_recommendations(self) -> List[Recommendation]:
        return self.recommendation_engine.generate(self.active_filters)

    def run_scenario(self, scenario: PolicyScenario) -> SimulationResult:
        return self.simulation_service.run_scenario(scenario, self.active_filters)

    def export_statistics_report(self, path: str) -> str:
        df = self.report_service.build_statistics_report(self.active_filters)
        return self.report_service.export(df, path)
