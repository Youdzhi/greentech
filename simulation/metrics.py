"""Shared status thresholds and simulation metrics."""

from dataclasses import dataclass
from enum import Enum


class Status(str, Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    FAILURE_RISK = "FAILURE"


class CascadeRisk(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


def get_status(utilisation: float) -> Status:
    """Map a ratio such as 0.85 to the product's shared status scale."""
    if utilisation < 0.70:
        return Status.NORMAL
    if utilisation < 0.85:
        return Status.WARNING
    if utilisation <= 1.0:
        return Status.HIGH
    if utilisation <= 1.20:
        return Status.CRITICAL
    return Status.FAILURE_RISK


def get_status_color(status: Status | str) -> str:
    """Return a hex color suitable for the dark control-room UI."""
    colors = {
        Status.NORMAL: "#27d17f",
        Status.WARNING: "#f4c542",
        Status.HIGH: "#ff9f43",
        Status.CRITICAL: "#ff5b5b",
        Status.FAILURE_RISK: "#ff2d55",
    }
    return colors.get(Status(status), "#9aa4b2")


@dataclass
class SimulationMetrics:
    """KPI snapshot consumed by UI and reporting code."""

    total_generation_mw: float = 0.0
    total_demand_mw: float = 0.0
    available_capacity_mw: float = 0.0
    network_utilisation: float = 0.0
    operational_assets: int = 0
    total_assets: int = 0
    critical_assets: int = 0
    failed_assets: int = 0
    predicted_failures: int = 0
    affected_consumers: int = 0
    critical_consumers_affected: int = 0
    cascade_risk: CascadeRisk = CascadeRisk.LOW
    cascade_duration_s: float = 0.0
