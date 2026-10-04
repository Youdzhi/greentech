"""Synthetic city aggregate and JSON serialization."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .consumer import Consumer
from .generator import Generator
from .power_line import PowerLine
from .substation import Substation


@dataclass
class City:
    """A complete synthetic electricity network dataset."""

    name: str
    generators: list[Generator] = field(default_factory=list)
    substations: list[Substation] = field(default_factory=list)
    consumers: list[Consumer] = field(default_factory=list)
    power_lines: list[PowerLine] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("City name must not be empty")

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable city mapping."""
        return {
            "name": self.name,
            "generators": [item.to_dict() for item in self.generators],
            "substations": [item.to_dict() for item in self.substations],
            "consumers": [item.to_dict() for item in self.consumers],
            "power_lines": [item.to_dict() for item in self.power_lines],
        }

    def to_json(self, destination: str | Path | None = None) -> str:
        """Serialize the city and optionally write it to a JSON file."""
        payload = json.dumps(self.to_dict(), indent=2)
        if destination is not None:
            Path(destination).write_text(payload + "\n", encoding="utf-8")
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "City":
        """Build a city from a mapping, converting malformed data to ValueError."""
        if not isinstance(data, dict):
            raise ValueError("City data must be a JSON object")
        try:
            return cls(
                name=data["name"],
                generators=[Generator.from_dict(item) for item in data.get("generators", [])],
                substations=[Substation.from_dict(item) for item in data.get("substations", [])],
                consumers=[Consumer.from_dict(item) for item in data.get("consumers", [])],
                power_lines=[PowerLine.from_dict(item) for item in data.get("power_lines", [])],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid city data: {exc}") from exc

    @classmethod
    def from_json(cls, source: str | Path) -> "City":
        """Load a city from JSON text or a JSON file path."""
        try:
            path = Path(source)
            if path.exists():
                payload = json.loads(path.read_text(encoding="utf-8"))
            else:
                payload = json.loads(str(source))
        except (OSError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError(f"Invalid city JSON: {exc}") from exc
        return cls.from_dict(payload)
