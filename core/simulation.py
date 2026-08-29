from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict
import pandas as pd

from .domain import PolicyScenario, SimulationResult
from .repository import DataRepository, FilterMap
from .statistics_service import StatisticsService


@dataclass
class SimulationService:
    """Runs 'what-if' policy simulations — applies restriction rules to the dataset and computes the simulated return rate."""
    repository: DataRepository
    statistics_service: StatisticsService

    def run_scenario(self, scenario: PolicyScenario, filters: FilterMap = None) -> SimulationResult:
        if filters is None:
            filters = {}
        if not scenario.validate():
            raise ValueError("Invalid policy scenario.")
        df = self.repository.load_dataset(filters)

        if df.empty:
            return SimulationResult(
                scenario_id=scenario.scenario_id,
                baseline_return_rate=0.0,
                simulated_return_rate=0.0,
                delta_return_rate=0.0,
                affected_return_count=0,
            )

        baseline = self._compute_baseline_return_rate(df)
        scenario_df = self._apply_scenario_rules(df, scenario)
        simulated = self._compute_simulated_return_rate(df, scenario_df)
        delta = simulated - baseline

        affected_returns = int(((df["is_returned"] == 1) & (scenario_df["restricted"] == 1)).sum())

        return SimulationResult(
            scenario_id=scenario.scenario_id,
            baseline_return_rate=float(baseline),
            simulated_return_rate=float(simulated),
            delta_return_rate=float(delta),
            affected_return_count=affected_returns,
        )

    def _compute_baseline_return_rate(self, df: pd.DataFrame) -> float:
        total = len(df)
        returned = int(df["is_returned"].sum())
        return float(returned) / float(total) if total else 0.0

    def _apply_scenario_rules(self, df: pd.DataFrame, scenario: PolicyScenario) -> pd.DataFrame:
        tmp = df.copy()
        tmp["restricted"] = 0

        if "markdown_percentage" in tmp.columns:
            tmp.loc[tmp["markdown_percentage"] >= scenario.markdown_threshold, "restricted"] = 1

        if scenario.excluded_categories and "category" in tmp.columns:
            tmp.loc[tmp["category"].isin(scenario.excluded_categories), "restricted"] = 1
        if scenario.excluded_brands and "brand" in tmp.columns:
            tmp.loc[tmp["brand"].isin(scenario.excluded_brands), "restricted"] = 1
        if scenario.excluded_seasons and "season" in tmp.columns:
            tmp.loc[tmp["season"].isin(scenario.excluded_seasons), "restricted"] = 1

        return tmp

    def _compute_simulated_return_rate(self, original_df: pd.DataFrame, scenario_df: pd.DataFrame) -> float:
        """
        Simple, dataset-aligned simulation:
        - Assume returns that fall under 'restricted' would be prevented/removed.
        - Simulated return count = original returns - restricted returns
        - Total purchases unchanged (conservative).
        """
        total = len(original_df)
        original_returns = int(original_df["is_returned"].sum())
        prevented = int(((original_df["is_returned"] == 1) & (scenario_df["restricted"] == 1)).sum())
        simulated_returns = max(0, original_returns - prevented)
        return float(simulated_returns) / float(total) if total else 0.0
