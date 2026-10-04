# LeSauveur

## Green Tech Hackathon — Team 23: **BigInt**

LeSauveur is a Python desktop MVP created by **Team 23, “BigInt”**, for a Green Tech energy hackathon.

The team selected the challenge of creating an easy way to collect, map, and show an electricity network — what exists, where it is, and what is under stress or broken.

> **Don't wait for the blackout. Simulate it first.**

## The solution

LeSauveur is a digital-twin prototype for a fictional urban electricity network. It represents generators, substations, consumers, and power lines, then simulates changing demand and infrastructure stress.

The application is designed to answer:

> **What happens to the electrical network when demand or infrastructure stress increases?**

The MVP demonstrates the following story:

```text
COLLECT → MAP → SIMULATE → IDENTIFY WEAK POINTS
        → FAILURE → CASCADE → IMPACT
```

Users can explore a synthetic city, activate stress scenarios such as a summer peak, identify vulnerable infrastructure, estimate time-to-failure, and observe how load redistribution can trigger cascading failures and affect consumers or critical infrastructure.

## Key capabilities

- Visualize a synthetic urban electricity network.
- Map generators, substations, consumer zones, and power lines.
- Simulate electricity demand and available generation.
- Calculate simplified infrastructure utilization.
- Highlight weak points and rank vulnerable assets.
- Estimate time-to-failure under sustained overload.
- Simulate infrastructure failures and load redistribution.
- Detect cascading failures and log cascade events.
- Show affected consumers and critical infrastructure.
- Compare “What If?” scenarios.
- Reset the network and run another scenario.

## Demonstration flow

1. Launch the application and display the operational synthetic city.
2. Select **Summer Peak** to increase demand.
3. Watch infrastructure move from green to yellow, orange, and red as stress increases.
4. Review vulnerable assets and time-to-failure estimates.
5. Press **Simulate**.
6. Observe the first failure, load redistribution, secondary overloads, and cascade events.
7. Review failed assets, affected consumers, critical infrastructure, and cascade risk.
8. Press **Reset** and run another scenario.

## Technology

- Python 3.11+
- PyQt6
- NetworkX
- NumPy
- JSON
- pytest

The simulation logic is kept separate from the PyQt user interface. The project is intended to run locally and does not require external map services, cloud infrastructure, authentication, or a database.

## Project structure

```text
.
├── main.py                 # Application entry point
├── app/                    # PyQt6 interface, map, controls, panels, and styles
├── simulation/             # Scenarios, power flow, failure, cascade, and metrics
├── models/                 # City, network asset, and event models
├── data/                   # Synthetic city and scenario data
├── tests/                  # Automated model and simulation tests
├── idea.md                # Original hackathon idea
└── SAVIOUR_Copilot_Implementation_Plan.md
                           # Detailed implementation plan
```

## Getting started

Create and activate a virtual environment, then install the dependencies:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Run the application:

```bash
python main.py
```

Run the test suite:

```bash
pytest
```

If PyQt6 is unavailable, `main.py` provides a headless stress-demo fallback and prints a reminder to install the dependencies.

## Scope and limitations

This is a hackathon simulation intended to be clear, explainable, and visually convincing. It is **not** an engineering-grade power-grid simulator and should not be used for operational decisions.

The model intentionally does not implement real AC power-flow equations, SCADA integration, protection-system physics, transformer electromagnetic models, or other production-grid functionality. The city and network are synthetic and should not be interpreted as a representation of a real Armenian electrical grid.

## Product positioning

LeSauveur helps communicate:

```text
Where is the infrastructure?
        ↓
How is it connected?
        ↓
Where is the stress?
        ↓
What breaks first?
        ↓
What happens next?
        ↓
Who gets affected?
```

## Team

**Team 23 — BigInt**

Created for the Green Tech energy hackathon.

