"""Deterministic overload damage and failure calculations."""

from models import PowerLine, Substation

DAMAGE_MULTIPLIER = 2.5


def utilisation(component: PowerLine | Substation) -> float:
    """Return component load divided by capacity."""
    capacity = component.max_capacity_mw
    return component.current_load_mw / capacity if capacity else float("inf")


def calculate_damage_rate(component: PowerLine | Substation) -> float:
    """Return damage points per simulated second."""
    return max(0.0, utilisation(component) - 1.0) * DAMAGE_MULTIPLIER


def update_damage(component: PowerLine | Substation, delta_time: float) -> float:
    """Accumulate damage and return the new value."""
    if component.operational:
        component.damage += calculate_damage_rate(component) * max(0.0, delta_time)
    return component.damage


def estimate_time_to_failure(component: PowerLine | Substation) -> float | None:
    """Estimate seconds until failure, or None when not overloaded."""
    rate = calculate_damage_rate(component)
    if rate <= 0 or not component.operational:
        return None
    return max(0.0, component.failure_limit - component.damage) / rate


def fail_component(component: PowerLine | Substation) -> bool:
    """Mark a damaged component failed and report whether state changed."""
    if component.operational and component.damage >= component.failure_limit:
        component.operational = False
        return True
    return False
