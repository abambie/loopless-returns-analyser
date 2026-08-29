from config import CSV_PATH, REQUIRED_COLS
from core.ml import FeatureEngineer, RiskPredictionModel, RiskPredictionService
from core.repository import DataRepository


def build_service(tmp_path):
    repository = DataRepository(backend="sqlite", sqlite_path=tmp_path / "test.db")
    repository.initialise(CSV_PATH, REQUIRED_COLS)
    engineer = FeatureEngineer(
        categorical_columns=["category", "brand", "season", "size", "color"],
        numeric_columns=[
            "original_price",
            "markdown_percentage",
            "current_price",
            "stock_quantity",
            "customer_rating",
        ],
    )
    return RiskPredictionService(repository, engineer, RiskPredictionModel())


def test_model_trains_and_scores(tmp_path):
    service = build_service(tmp_path)
    metrics = service.train_model()

    assert set(metrics) == {
        "accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
        "confusion_matrix",
        "feature_count",
    }
    assert all(0.0 <= metrics[name] <= 1.0 for name in ["accuracy", "precision", "recall", "f1", "roc_auc"])
    assert metrics["feature_count"] > 5

    scored = service.score_risk()
    assert len(scored) == 2200
    assert scored["risk_score"].between(0.0, 1.0).all()
