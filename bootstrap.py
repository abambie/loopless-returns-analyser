"""Build the repository and application services used by the Dash pages."""

from __future__ import annotations

import os

import joblib

from config import CSV_PATH, DB_BACKEND, MODEL_DIR, REQUIRED_COLS
from core.controller import DashboardController
from core.ml import FeatureEngineer, RiskPredictionModel, RiskPredictionService
from core.recommendations import RecommendationEngine
from core.reporting import CSVExporter, ReportService
from core.repository import DataRepository
from core.simulation import SimulationService
from core.statistics_service import StatisticsService


def build_repository() -> DataRepository:
    repository = DataRepository()
    row_count = repository.initialise(CSV_PATH, REQUIRED_COLS)
    print(f"[OK] {DB_BACKEND.title()} database ready - {row_count} records loaded.")
    return repository


def build_controller(repository: DataRepository) -> DashboardController:
    statistics_service = StatisticsService(repository=repository)
    feature_engineer = FeatureEngineer(
        categorical_columns=["category", "brand", "season", "size", "color"],
        numeric_columns=[
            "original_price",
            "markdown_percentage",
            "current_price",
            "stock_quantity",
            "customer_rating",
        ],
    )
    risk_service = RiskPredictionService(
        repository=repository,
        feature_engineer=feature_engineer,
        model=RiskPredictionModel(),
    )
    simulation_service = SimulationService(
        repository=repository,
        statistics_service=statistics_service,
    )
    recommendation_engine = RecommendationEngine(
        statistics_service=statistics_service,
        risk_service=risk_service,
    )
    report_service = ReportService(
        statistics_service=statistics_service,
        risk_service=risk_service,
        exporter=CSVExporter(),
    )
    return DashboardController(
        statistics_service=statistics_service,
        risk_service=risk_service,
        recommendation_engine=recommendation_engine,
        simulation_service=simulation_service,
        report_service=report_service,
    )


repo = build_repository()
ctrl = build_controller(repo)

MODEL_PATH = MODEL_DIR / "model.joblib"
FE_PATH = MODEL_DIR / "feature_engineer.joblib"
os.makedirs(MODEL_DIR, exist_ok=True)

if MODEL_PATH.exists() and FE_PATH.exists():
    try:
        ctrl.risk_service.model.load(MODEL_PATH)
        ctrl.risk_service.feature_engineer = joblib.load(FE_PATH)
        print("[INFO] Loaded saved ML model from disk.")
    except (OSError, ValueError, TypeError) as load_error:
        print(f"[WARNING] Could not load saved model: {load_error}")
