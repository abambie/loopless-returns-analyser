"""Reproducible model comparison and customer-segment clustering experiment."""

from __future__ import annotations

import json
import os
from pathlib import Path

# Keeps local and CI runs deterministic on hosts that cannot report physical cores.
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    silhouette_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "fashion_boutique_dataset_with_return_date.csv"
OUTPUT = ROOT / "docs" / "model_results.json"

CATEGORICAL_FEATURES = ["category", "brand", "season", "size", "color"]
NUMERIC_FEATURES = [
    "original_price",
    "markdown_percentage",
    "current_price",
    "stock_quantity",
    "customer_rating",
]
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES


def load_data() -> tuple[pd.DataFrame, pd.Series]:
    df = pd.read_csv(DATASET)
    df["is_returned"] = df["is_returned"].map(
        lambda value: 1 if str(value).strip().lower() in {"1", "true", "yes"} else 0
    )
    df = df.dropna(subset=FEATURES + ["is_returned"]).copy()
    return df[FEATURES], df["is_returned"].astype(int)


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
            ("numeric", StandardScaler(), NUMERIC_FEATURES),
        ]
    )


def evaluate_model(model: object, x_train: pd.DataFrame, x_test: pd.DataFrame,
                   y_train: pd.Series, y_test: pd.Series) -> dict[str, float]:
    pipeline = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor()),
            ("model", model),
        ]
    )
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    probabilities = pipeline.predict_proba(x_test)[:, 1]
    return {
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "precision": round(float(precision_score(y_test, predictions, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, predictions, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, predictions, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 4),
    }


def cluster_profiles(df: pd.DataFrame, target: pd.Series) -> dict[str, object]:
    numeric = df[NUMERIC_FEATURES].copy()
    scaled = StandardScaler().fit_transform(numeric)
    model = KMeans(n_clusters=4, n_init=10, random_state=42)
    labels = model.fit_predict(scaled)

    profiles = numeric.copy()
    profiles["cluster"] = labels
    profiles["is_returned"] = target.to_numpy()
    summary = profiles.groupby("cluster").agg(
        records=("is_returned", "size"),
        return_rate=("is_returned", "mean"),
        average_price=("current_price", "mean"),
        average_markdown=("markdown_percentage", "mean"),
        average_rating=("customer_rating", "mean"),
    )
    return {
        "cluster_count": 4,
        "silhouette_score": round(float(silhouette_score(scaled, labels)), 4),
        "profiles": {
            str(index): {
                key: round(float(value), 4)
                for key, value in row.items()
            }
            for index, row in summary.to_dict(orient="index").items()
        },
    }


def main() -> None:
    features, target = load_data()
    x_train, x_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=0.2,
        random_state=42,
        stratify=target,
    )

    results = {
        "dataset": {
            "rows": int(len(features)),
            "return_rate": round(float(target.mean()), 4),
            "test_rows": int(len(x_test)),
            "random_state": 42,
        },
        "classification": {
            "logistic_regression": evaluate_model(
                LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42),
                x_train,
                x_test,
                y_train,
                y_test,
            ),
            "random_forest": evaluate_model(
                RandomForestClassifier(
                    n_estimators=300,
                    class_weight="balanced",
                    random_state=42,
                    n_jobs=1,
                ),
                x_train,
                x_test,
                y_train,
                y_test,
            ),
        },
        "clustering": cluster_profiles(features, target),
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
