"""Cascade event domain model."""

from dataclasses import asdict, dataclass, field


@dataclass
class CascadeEvent:
    """A timestamped event emitted while a network cascade is simulated."""

    timestamp: float
    component_id: str
    component_type: str
    previous_load_mw: float
    utilisation: float
    reason: str
    affected_consumers: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.component_id.strip():
            raise ValueError("Cascade-event component id must not be empty")
        if self.timestamp < 0 or self.previous_load_mw < 0 or self.utilisation < 0:
            raise ValueError("Cascade-event numeric values must not be negative")

    def to_dict(self) -> dict:
        """Return a JSON-serializable representation."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "CascadeEvent":
        """Create an event from a mapping, with validation."""
        try:
            return cls(**data)
        except (TypeError, KeyError, ValueError) as exc:
            raise ValueError(f"Invalid cascade-event data: {exc}") from exc
