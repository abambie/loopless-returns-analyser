from config import CSV_PATH, REQUIRED_COLS
from core.domain import PolicyScenario
from core.repository import DataRepository
from core.simulation import SimulationService
from core.statistics_service import StatisticsService


def test_policy_simulation_reduces_or_preserves_return_rate(tmp_path):
    repository = DataRepository(backend="sqlite", sqlite_path=tmp_path / "test.db")
    repository.initialise(CSV_PATH, REQUIRED_COLS)
    service = SimulationService(repository, StatisticsService(repository))
    scenario = PolicyScenario(
        scenario_id="test",
        name="Test policy",
        markdown_threshold=30,
        excluded_categories=["Dresses"],
        excluded_brands=[],
        excluded_seasons=[],
    )

    result = service.run_scenario(scenario)
    assert result.simulated_return_rate <= result.baseline_return_rate
    assert result.affected_return_count >= 0
