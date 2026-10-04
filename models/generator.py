"""Generator domain model."""

from dataclasses import asdict, dataclass


@dataclass
class Generator:
    """A dispatchable electricity source in the synthetic city."""

    id: str
    name: str
    x: float
    y: float
    capacity_mw: float
    current_output_mw: float = 0.0
    operational: bool = True

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Generator id must not be empty")
        if self.capacity_mw < 0:
            raise ValueError("Generator capacity must not be negative")
        if self.current_output_mw < 0:
            raise ValueError("Generator output must not be negative")
        if self.current_output_mw > self.capacity_mw:
            raise ValueError("Generator output cannot exceed capacity")

    def to_dict(self) -> dict:
        """Return a JSON-serializable representation."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Generator":
        """Create a generator from a mapping, with a useful validation error."""
        try:
            return cls(**data)
        except (TypeError, KeyError, ValueError) as exc:
            raise ValueError(f"Invalid generator data: {exc}") from exc
