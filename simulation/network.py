"""NetworkX representation of a City."""

from __future__ import annotations

import networkx as nx

from models import City


class NetworkModel:
    """Builds and queries the operational topology for a city."""

    def __init__(self, city: City) -> None:
        self.city = city
        self.graph: nx.Graph = nx.Graph()
        self.rebuild()

    def rebuild(self) -> None:
        self.graph.clear()
        for item in (*self.city.generators, *self.city.substations, *self.city.consumers):
            if getattr(item, "operational", True):
                self.graph.add_node(item.id, kind=type(item).__name__.lower(), model=item)
        for line in self.city.power_lines:
            if line.operational and line.from_node in self.graph and line.to_node in self.graph:
                self.graph.add_edge(
                    line.from_node,
                    line.to_node,
                    id=line.id,
                    model=line,
                    capacity=line.max_capacity_mw,
                    current_load=line.current_load_mw,
                    length=line.length_km,
                )

    def operational_paths(self, source: str, target: str) -> list[list[str]]:
        """Return deterministic shortest paths between operational assets."""
        if source not in self.graph or target not in self.graph:
            return []
        try:
            return list(nx.all_shortest_paths(self.graph, source, target, weight="length"))
        except nx.NetworkXNoPath:
            return []

    def disconnected_consumers(self) -> list[str]:
        """Return consumer ids that cannot reach any operational generator."""
        sources = [item.id for item in self.city.generators if item.operational and item.id in self.graph]
        disconnected = []
        for consumer in self.city.consumers:
            if not consumer.id in self.graph or not any(
                nx.has_path(self.graph, source, consumer.id) for source in sources
            ):
                disconnected.append(consumer.id)
        return disconnected

    def remove_failed_infrastructure(self) -> None:
        """Refresh topology after model operational flags change."""
        self.rebuild()
