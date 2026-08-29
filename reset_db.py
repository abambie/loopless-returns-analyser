"""Rebuild the configured database from the bundled CSV dataset."""

from config import CSV_PATH, MODEL_DIR, REQUIRED_COLS
from core.repository import DataRepository


def main() -> None:
    repository = DataRepository()
    row_count = repository.reset_from_csv(CSV_PATH, REQUIRED_COLS)
    repository.close()

    for name in ("model.joblib", "feature_engineer.joblib"):
        path = MODEL_DIR / name
        if path.exists():
            path.unlink()

    print(f"Database rebuilt successfully with {row_count} rows.")
    print("Run python app.py and select 'Analyse My Products' to retrain the model.")


if __name__ == "__main__":
    main()
