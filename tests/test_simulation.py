"""Backend integration tests for the LeSauveur simulation."""

from pathlib import Path

from models import City, PowerLine, Substation
from simulation import Scenario, SimulationEngine, Status, get_status
from simulation.failure_model import calculate_damage_rate, estimate_time_to_failure, update_damage
from simulation.network import NetworkModel


CITY_PATH = Path(__file__).parents[1] / "data" / "city.json"


def load_engine() -> SimulationEngine:
    return SimulationEngine(City.from_json(CITY_PATH))


def test_status_thresholds_are_centralized() -> None:
    assert get_status(0.69) == Status.NORMAL
    assert get_status(0.70) == Status.WARNING
    assert get_status(0.85) == Status.HIGH
    assert get_status(1.01) == Status.CRITICAL
    assert get_status(1.21) == Status.FAILURE_RISK


def test_network_builds_and_finds_disconnected_consumers() -> None:
    city = City.from_json(CITY_PATH)
    network = NetworkModel(city)
    assert len(network.graph.nodes) == 21
    assert len(network.graph.edges) == 28
    assert network.disconnected_consumers() == []


def test_normal_scenario_has_demand_and_generation() -> None:
    engine = load_engine()
    engine.run_scenario(Scenario("Normal", 1.0))
    metrics = engine.get_metrics()
    assert metrics.total_demand_mw > 0
    assert metrics.total_generation_mw == metrics.total_demand_mw
    assert metrics.failed_assets == 0


def test_engine_initializes_live_demand_from_base_demand() -> None:
    engine = load_engine()
    metrics = engine.get_metrics()
    assert metrics.total_demand_mw > 0
    assert metrics.total_generation_mw == metrics.total_demand_mw
    assert metrics.network_utilisation > 0


def test_overload_damage_and_time_to_failure() -> None:
    line = PowerLine("l", "a", "b", 10, current_load_mw=15, failure_limit=10)
    assert calculate_damage_rate(line) == 1.25
    assert estimate_time_to_failure(line) == 8.0
    update_damage(line, 2)
    assert line.damage == 2.5


def test_failed_substation_disconnects_its_direct_consumer_when_no_route() -> None:
    city = City.from_json(CITY_PATH)
    city.substations[0].operational = False
    network = NetworkModel(city)
    assert "c1" in network.disconnected_consumers()


def test_what_if_does_not_mutate_current_engine() -> None:
    engine = load_engine()
    before = engine.get_metrics()
    result = engine.simulate_what_if(Scenario("Failure", failed_substation_id="s4"))
    assert engine.get_metrics() == before
    assert result.get_metrics().failed_assets >= 1 or result.get_metrics().affected_consumers >= 0


def test_summer_peak_increases_demand() -> None:
    engine = load_engine()
    normal = engine.get_metrics().total_demand_mw
    engine.run_scenario(Scenario("Summer Peak", demand_multiplier=1.35))
    assert engine.get_metrics().total_demand_mw > normal
