from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict
import pandas as pd

from .statistics_service import StatisticsService
from .ml import RiskPredictionService
from .domain import SimulationResult


@dataclass
class CSVExporter:
    """Thin wrapper around pandas to_csv — encapsulates CSV export settings in one place."""
    delimiter: str = ","
    include_headers: bool = True

    def export_dataframe(self, df: pd.DataFrame, path: str) -> str:
        df.to_csv(path, index=False, sep=self.delimiter, header=self.include_headers)
        return path


@dataclass
class ReportService:
    """Assembles reports as DataFrames and delegates the actual file writing to CSVExporter."""
    statistics_service: StatisticsService
    risk_service: RiskPredictionService
    exporter: CSVExporter

    def build_statistics_report(self, filters: Dict[str, Any]) -> pd.DataFrame:
        stats = self.statistics_service.get_statistics(filters)
        return pd.DataFrame([stats])

    def build_return_reason_report(self, filters: Dict[str, Any]) -> pd.DataFrame:
        rows = self.statistics_service.get_return_reason_breakdown(filters)
        return pd.DataFrame(rows)

    def build_high_risk_products_report(self, top_n: int, filters: Dict[str, Any]) -> pd.DataFrame:
        rows = self.risk_service.get_high_risk_products(top_n, filters)
        return pd.DataFrame(rows)

    def build_simulation_report(self, result: SimulationResult) -> pd.DataFrame:
        return pd.DataFrame([result.to_dict()])

    def export(self, report_df: pd.DataFrame, path: str) -> str:
        return self.exporter.export_dataframe(report_df, path)
