"""Predefined and custom scenario definitions."""

from __future__ import annotations

from dataclasses import dataclass

from models import City


@dataclass(frozen=True)
class Scenario:
    """A deterministic demand/generation modification."""

    name: str
    demand_multiplier: float = 1.0
    generation_multiplier: float = 1.0
    failed_substation_id: str | None = None
    failed_generator_id: str | None = None
    industrial_multiplier: float = 1.0
    demand_add_mw: float = 0.0
    generation_add_mw: float = 0.0
    battery_storage_mw: float = 0.0


class ScenarioEngine:
    """Applies scenario definitions without owning simulation state."""

    PRESETS: dict[str, Scenario] = {}

    @classmethod
    def get(cls, name: str) -> Scenario:
        return cls.PRESETS.get(name, Scenario(name or "Custom scenario"))

    @staticmethod
    def apply(city: City, scenario: Scenario) -> None:
        """Apply scenario values to a city in-place."""
        for generator in city.generators:
            generator.operational = generator.id != scenario.failed_generator_id
            generator.capacity_mw = (
                generator.capacity_mw * scenario.generation_multiplier
                + scenario.generation_add_mw / max(1, len(city.generators))
                + scenario.battery_storage_mw / max(1, len(city.generators))
            )
        for substation in city.substations:
            if substation.id == scenario.failed_substation_id:
                substation.operational = False
        for consumer in city.consumers:
            multiplier = scenario.demand_multiplier
            if "industrial" in consumer.name.lower():
                multiplier *= scenario.industrial_multiplier
            consumer.current_demand_mw = (
                consumer.base_demand_mw * multiplier
                + scenario.demand_add_mw / max(1, len(city.consumers))
            )
