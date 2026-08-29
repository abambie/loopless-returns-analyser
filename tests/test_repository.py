from config import CSV_PATH, REQUIRED_COLS
from core.repository import DataRepository
from core.statistics_service import StatisticsService


def test_sqlite_repository_imports_dataset(tmp_path):
    repository = DataRepository(backend="sqlite", sqlite_path=tmp_path / "test.db")
    row_count = repository.initialise(CSV_PATH, REQUIRED_COLS)

    assert row_count == 2200
    assert len(repository.load_dataset()) == 2200
    assert repository.get_date_range() == ("2024-01-01", "2025-12-31")


def test_statistics_match_bundled_dataset(tmp_path):
    repository = DataRepository(backend="sqlite", sqlite_path=tmp_path / "test.db")
    repository.initialise(CSV_PATH, REQUIRED_COLS)
    statistics = StatisticsService(repository)

    result = statistics.get_statistics({})
    assert result["total_records"] == 2200
    assert result["returned_records"] == 598
    assert round(result["overall_return_rate"], 4) == 0.2718
