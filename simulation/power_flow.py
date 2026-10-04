"""Explainable graph-based power distribution."""

from __future__ import annotations

from models import City

from .network import NetworkModel


def calculate_power_flow(city: City, network: NetworkModel) -> list[str]:
    """Distribute consumer demand over deterministic shortest paths.

    This is intentionally not an electrical power-flow solver. Each consumer's
    demand is assigned to the shortest available generator path, and shared
    load is accumulated on lines and substations.
    """
    for line in city.power_lines:
        line.current_load_mw = 0.0
    for substation in city.substations:
        substation.current_load_mw = 0.0

    available = sum(g.capacity_mw for g in city.generators if g.operational)
    demand = sum(c.current_demand_mw for c in city.consumers)
    scale = min(1.0, available / demand) if demand > 0 else 1.0
    for generator in city.generators:
        generator.current_output_mw = 0.0

    disconnected: list[str] = []
    sources = [g for g in city.generators if g.operational]
    for consumer in sorted(city.consumers, key=lambda item: item.id):
        paths: list[tuple[float, object, list[str]]] = []
        for generator in sources:
            for path in network.operational_paths(generator.id, consumer.id)[:1]:
                length = sum(
                    network.graph.edges[a, b]["length"] for a, b in zip(path, path[1:])
                )
                paths.append((length, generator, path))
        if not paths:
            disconnected.append(consumer.id)
            continue
        _, generator, path = min(paths, key=lambda item: (item[0], item[1].id))
        served = consumer.current_demand_mw * scale
        generator.current_output_mw += served
        for node in path:
            if node in {sub.id for sub in city.substations}:
                next(item for item in city.substations if item.id == node).current_load_mw += served
        for a, b in zip(path, path[1:]):
            line = network.graph.edges[a, b]["model"]
            line.current_load_mw += served
    return disconnected
