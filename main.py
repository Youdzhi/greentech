"""LeSauveur application entry point."""

from pathlib import Path

from models import City


def main() -> int:
    city = City.from_json(Path(__file__).parent / "data" / "city.json")
    try:
        from app.main_window import run_app
    except ModuleNotFoundError as exc:
        if exc.name == "PyQt6":
            engine_demo(city)
            print("\nPyQt6 is not installed. Install dependencies with: python -m pip install -r requirements.txt")
            return 0
        raise
    return run_app(city)


def engine_demo(city: City) -> None:
    """Provide a useful headless smoke demo when desktop dependencies are absent."""
    from simulation import Scenario, SimulationEngine

    engine = SimulationEngine(city)
    engine.run_scenario(Scenario("Headless stress demo", demand_multiplier=1.35))
    for _ in range(10):
        engine.tick(1.0)
    metrics = engine.get_metrics()
    print(
        f"LeSauveur headless demo | demand={metrics.total_demand_mw:.0f} MW | "
        f"utilisation={metrics.network_utilisation:.0%} | failed={metrics.failed_assets}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
