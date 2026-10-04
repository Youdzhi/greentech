"""Substation domain model."""

from dataclasses import asdict, dataclass


@dataclass
class Substation:
    """A network substation whose load and damage are simulated."""

    id: str
    name: str
    x: float
    y: float
    max_capacity_mw: float
    current_load_mw: float = 0.0
    operational: bool = True
    damage: float = 0.0
    failure_limit: float = 100.0

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Substation id must not be empty")
        if self.max_capacity_mw <= 0:
            raise ValueError("Substation capacity must be greater than zero")
        if self.current_load_mw < 0:
            raise ValueError("Substation load must not be negative")
        if self.damage < 0:
            raise ValueError("Substation damage must not be negative")
        if self.failure_limit <= 0:
            raise ValueError("Substation failure limit must be greater than zero")

    def to_dict(self) -> dict:
        """Return a JSON-serializable representation."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Substation":
        """Create a substation from a mapping, with validation."""
        try:
            return cls(**data)
        except (TypeError, KeyError, ValueError) as exc:
            raise ValueError(f"Invalid substation data: {exc}") from exc
