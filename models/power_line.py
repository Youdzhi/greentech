"""Power-line domain model."""

from dataclasses import asdict, dataclass


@dataclass
class PowerLine:
    """An edge connecting two electrical-network assets."""

    id: str
    from_node: str
    to_node: str
    max_capacity_mw: float
    current_load_mw: float = 0.0
    length_km: float = 0.0
    operational: bool = True
    damage: float = 0.0
    failure_limit: float = 100.0

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Power-line id must not be empty")
        if not self.from_node.strip() or not self.to_node.strip():
            raise ValueError("Power-line endpoints must not be empty")
        if self.from_node == self.to_node:
            raise ValueError("Power-line endpoints must be different")
        if self.max_capacity_mw <= 0:
            raise ValueError("Power-line capacity must be greater than zero")
        if self.current_load_mw < 0 or self.length_km < 0 or self.damage < 0:
            raise ValueError("Power-line load, length, and damage must not be negative")
        if self.failure_limit <= 0:
            raise ValueError("Power-line failure limit must be greater than zero")

    def to_dict(self) -> dict:
        """Return a JSON-serializable representation."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PowerLine":
        """Create a power line from a mapping, with validation."""
        try:
            return cls(**data)
        except (TypeError, KeyError, ValueError) as exc:
            raise ValueError(f"Invalid power-line data: {exc}") from exc
