from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List
import pandas as pd

from .repository import DataRepository, FilterMap


@dataclass
class StatisticsService:
    """Computes live statistics (return rate, totals, averages, breakdowns) from the database."""
    repository: DataRepository

    def get_statistics(self, filters: FilterMap) -> Dict[str, Any]:
        df = self.repository.load_dataset(filters)

        if df.empty:
            return {
                "total_records": 0,
                "returned_records": 0,
                "overall_return_rate": 0.0,
                "avg_markdown_percentage": None,
                "avg_customer_rating": None,
                "avg_current_price": None,
            }

        total = len(df)
        returned = int(df["is_returned"].sum()) if "is_returned" in df.columns else 0
        rate = self._safe_div(returned, total)

        return {
            "total_records": total,
            "returned_records": returned,
            "overall_return_rate": rate,
            "avg_markdown_percentage": float(df["markdown_percentage"].mean()) if "markdown_percentage" in df.columns else None,
            "avg_customer_rating": float(df["customer_rating"].mean()) if "customer_rating" in df.columns else None,
            "avg_current_price": float(df["current_price"].mean()) if "current_price" in df.columns else None,
        }

    def get_return_reason_breakdown(self, filters: FilterMap) -> List[Dict[str, Any]]:
        df = self.repository.load_dataset(filters)
        if df.empty:
            return []
        df = df[df["is_returned"] == 1]
        if df.empty:
            return []
        counts = df["return_reason"].fillna("Unknown").value_counts().reset_index()
        counts.columns = ["return_reason", "count"]
        return counts.to_dict(orient="records")

    def get_return_rate_by_field(self, field: str, filters: FilterMap) -> List[Dict[str, Any]]:
        df = self.repository.load_dataset(filters)
        if df.empty or field not in df.columns:
            return []
        grp = df.groupby(field)["is_returned"].agg(["mean", "count"]).reset_index()
        grp.rename(columns={"mean": "return_rate", "count": "records"}, inplace=True)
        return grp.sort_values("return_rate", ascending=False).to_dict(orient="records")

    def get_return_trend_over_time(self, granularity: str, filters: FilterMap) -> List[Dict[str, Any]]:
        df = self.repository.load_dataset(filters)
        if df.empty or "purchase_date" not in df.columns:
            return []

        df = df.dropna(subset=["purchase_date"])
        dt = pd.to_datetime(df["purchase_date"])

        if granularity == "daily":
            bucket = dt.dt.to_period("D").astype(str)
        elif granularity == "weekly":
            bucket = dt.dt.to_period("W").astype(str)
        else:
            bucket = dt.dt.to_period("M").astype(str)

        tmp = df.copy()
        tmp["bucket"] = bucket
        grp = tmp.groupby("bucket")["is_returned"].agg(["mean", "count"]).reset_index()
        grp.rename(columns={"mean": "return_rate", "count": "records"}, inplace=True)
        return grp.sort_values("bucket").to_dict(orient="records")

    def _safe_div(self, a: float, b: float) -> float:
        return float(a) / float(b) if b else 0.0
