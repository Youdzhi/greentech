"""Phase 1 tests for LeSauveur domain models."""

import json

import pytest

from models import CascadeEvent, City, Consumer, Generator, PowerLine, Substation


def test_models_have_safe_defaults() -> None:
    assert Generator("g1", "Solar", 1, 2, 10).operational
    assert Substation("s1", "North", 1, 2, 20).failure_limit == 100
    assert Consumer("c1", "Homes", 1, 2, 5).current_demand_mw == 0
    assert PowerLine("l1", "g1", "s1", 10).operational
    assert CascadeEvent(0, "s1", "substation", 0, 0, "test").affected_consumers == []


def test_consumer_priority_is_validated_and_normalized() -> None:
    assert Consumer("c1", "Hospital", 0, 0, 5, priority="CRITICAL").priority == "CRITICAL"
    with pytest.raises(ValueError, match="priority"):
        Consumer("c1", "Unknown", 0, 0, 5, priority="URGENT")


def test_city_round_trip_json() -> None:
    city = City(
        "Demo City",
        generators=[Generator("g1", "Solar", 1, 2, 50, 20)],
        substations=[Substation("s1", "North", 3, 4, 40, 15)],
        consumers=[Consumer("c1", "Hospital", 5, 6, 10, 10, "CRITICAL")],
        power_lines=[PowerLine("l1", "g1", "s1", 40, 15, 2.5)],
    )

    restored = City.from_json(city.to_json())

    assert restored == city
    assert json.loads(city.to_json())["name"] == "Demo City"


def test_city_can_write_and_read_json_file(tmp_path) -> None:
    path = tmp_path / "city.json"
    original = City("File City", consumers=[Consumer("c1", "Homes", 0, 0, 2)])

    original.to_json(path)

    assert City.from_json(path) == original


@pytest.mark.parametrize(
    "factory",
    [
        lambda: Generator("g", "bad", 0, 0, -1),
        lambda: Substation("s", "bad", 0, 0, 0),
        lambda: Consumer("c", "bad", 0, 0, -1),
        lambda: PowerLine("l", "a", "b", 0),
        lambda: CascadeEvent(-1, "x", "line", 0, 0, "bad"),
    ],
)
def test_models_reject_invalid_data(factory) -> None:
    with pytest.raises(ValueError):
        factory()


def test_malformed_city_json_raises_domain_error() -> None:
    with pytest.raises(ValueError, match="Invalid city JSON"):
        City.from_json("{not-json")


def test_missing_city_fields_raise_domain_error() -> None:
    with pytest.raises(ValueError, match="Invalid city data"):
        City.from_dict({"generators": []})
