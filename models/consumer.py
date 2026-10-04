"""Consumer domain model."""

from dataclasses import asdict, dataclass
from enum import Enum


class ConsumerPriority(str, Enum):
    """Operational importance of an aggregated consumer zone."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"


@dataclass
class Consumer:
    """An aggregated electricity-consuming zone."""

    id: str
    name: str
    x: float
    y: float
    base_demand_mw: float
    current_demand_mw: float = 0.0
    priority: str = ConsumerPriority.NORMAL.value

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Consumer id must not be empty")
        if self.base_demand_mw < 0 or self.current_demand_mw < 0:
            raise ValueError("Consumer demand must not be negative")
        try:
            self.priority = ConsumerPriority(self.priority).value
        except ValueError as exc:
            raise ValueError(f"Invalid consumer priority: {self.priority}") from exc

    def to_dict(self) -> dict:
        """Return a JSON-serializable representation."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Consumer":
        """Create a consumer from a mapping, with validation."""
        try:
            return cls(**data)
        except (TypeError, KeyError, ValueError) as exc:
            raise ValueError(f"Invalid consumer data: {exc}") from exc
