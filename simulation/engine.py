"""High-level simulation orchestration API."""

from __future__ import annotations

import copy

from models import CascadeEvent, City, ConsumerPriority

from .failure_model import (
    estimate_time_to_failure,
    fail_component,
    update_damage,
    utilisation,
)
from .metrics import CascadeRisk, SimulationMetrics, Status, get_status
from .network import NetworkModel
from .power_flow import calculate_power_flow
from .scenarios import Scenario, ScenarioEngine


class SimulationEngine:
    """Runs deterministic demand, damage, and cascade simulations."""

    def __init__(self, city: City | None = None) -> None:
        self.city = copy.deepcopy(city) if city else City("Empty City")
        self._initial_city = copy.deepcopy(self.city)
        self._restore_base_operating_state()
        self.network = NetworkModel(self.city)
        self.events: list[CascadeEvent] = []
        self.simulation_time = 0.0
        self.disconnected: list[str] = []
        self.calculate_power_flow()

    def load_city(self, city: City) -> None:
        self.city = copy.deepcopy(city)
        self._restore_base_operating_state()
        self._initial_city = copy.deepcopy(city)
        self.reset()

    def reset(self) -> None:
        self.city = copy.deepcopy(self._initial_city)
        self._restore_base_operating_state()
        self.network = NetworkModel(self.city)
        self.events.clear()
        self.simulation_time = 0.0
        self.calculate_power_flow()

    def _restore_base_operating_state(self) -> None:
        """Initialize live demand from the city's base demand.

        Imported/demo JSON commonly omits transient current-demand values.
        Without this normalization, the first power-flow calculation sees a
        zero-load city and the UI appears inactive until a scenario is run.
        """
        for consumer in self.city.consumers:
            if consumer.current_demand_mw <= 0 and consumer.base_demand_mw > 0:
                consumer.current_demand_mw = consumer.base_demand_mw
        for generator in self.city.generators:
            if generator.current_output_mw < 0:
                generator.current_output_mw = 0.0

    def run_scenario(self, scenario: Scenario) -> None:
        self.reset()
        ScenarioEngine.apply(self.city, scenario)
        self.network.remove_failed_infrastructure()
        self.calculate_power_flow()
        self.events.append(CascadeEvent(self.simulation_time, scenario.name, "scenario", 0, 0, "Scenario activated"))

    def calculate_power_flow(self) -> None:
        self.disconnected = calculate_power_flow(self.city, self.network)

    def tick(self, delta_time: float) -> list[CascadeEvent]:
        """Advance time, update damage, and run any resulting cascade."""
        self.simulation_time += max(0.0, delta_time)
        for component in (*self.city.substations, *self.city.power_lines):
            update_damage(component, delta_time)
        return self.run_cascade()

    def run_cascade(self, max_iterations: int = 12) -> list[CascadeEvent]:
        """Fail damaged assets, recalculate flow, and repeat to stability."""
        new_events: list[CascadeEvent] = []
        for _ in range(max_iterations):
            candidates = [*self.city.substations, *self.city.power_lines]
            failed = [item for item in candidates if fail_component(item)]
            if not failed:
                break
            for component in failed:
                component_type = "substation" if component in self.city.substations else "power_line"
                event = CascadeEvent(
                    self.simulation_time,
                    component.id,
                    component_type,
                    component.current_load_mw,
                    utilisation(component),
                    "Sustained overload exceeded failure limit",
                    list(self.disconnected),
                )
                self.events.append(event)
                new_events.append(event)
            self.network.remove_failed_infrastructure()
            self.calculate_power_flow()
            for component in (*self.city.substations, *self.city.power_lines):
                update_damage(component, 1.0)
        return new_events

    def get_metrics(self) -> SimulationMetrics:
        operational = [*self.city.generators, *self.city.substations, *self.city.power_lines]
        failed = [item for item in operational if not item.operational]
        critical = [
            item for item in (*self.city.substations, *self.city.power_lines)
            if item.operational and get_status(utilisation(item)) in {Status.CRITICAL, Status.FAILURE_RISK}
        ]
        generation = sum(g.current_output_mw for g in self.city.generators if g.operational)
        demand = sum(c.current_demand_mw for c in self.city.consumers)
        ratios = [utilisation(item) for item in (*self.city.substations, *self.city.power_lines) if item.operational]
        # The maximum stressed component is the meaningful network KPI for
        # this explainable MVP: a single overloaded substation can trigger a
        # cascade even when the city-wide average looks healthy.
        avg_utilisation = max(ratios, default=0.0)
        affected_ids = set(self.disconnected)
        risk = CascadeRisk.LOW
        if avg_utilisation > 1.2 or failed:
            risk = CascadeRisk.CRITICAL
        elif avg_utilisation > 1.0:
            risk = CascadeRisk.HIGH
        elif avg_utilisation >= 0.85:
            risk = CascadeRisk.MEDIUM
        critical_affected = sum(
            1 for item in self.city.consumers
            if item.id in affected_ids and item.priority == ConsumerPriority.CRITICAL.value
        )
        predicted_failures = sum(
            estimate_time_to_failure(item) is not None
            for item in (*self.city.substations, *self.city.power_lines)
            if item.operational
        )
        return SimulationMetrics(
            total_generation_mw=generation,
            total_demand_mw=demand,
            available_capacity_mw=sum(
                item.max_capacity_mw for item in self.city.substations if item.operational
            ),
            network_utilisation=avg_utilisation,
            operational_assets=sum(item.operational for item in operational),
            total_assets=len(operational),
            critical_assets=len(critical),
            failed_assets=len(failed),
            predicted_failures=predicted_failures,
            affected_consumers=len(affected_ids),
            critical_consumers_affected=critical_affected,
            cascade_risk=risk,
            cascade_duration_s=self.simulation_time,
        )

    def get_vulnerable_assets(self, limit: int = 5) -> list[tuple[object, float, float | None]]:
        """Return operational assets ordered by utilisation and failure estimate."""
        items = [*self.city.substations, *self.city.power_lines]
        return sorted(
            [(item, utilisation(item), estimate_time_to_failure(item)) for item in items if item.operational],
            key=lambda row: row[1],
            reverse=True,
        )[:limit]

    def simulate_what_if(self, scenario: Scenario) -> "SimulationEngine":
        """Run a scenario on a cloned engine, preserving the current state."""
        clone = SimulationEngine(self.city)
        clone.run_scenario(scenario)
        for _ in range(60):
            clone.tick(1.0)
            if clone.get_metrics().failed_assets:
                break
        return clone
