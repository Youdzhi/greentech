# LeSauveur — GitHub Copilot Implementation Plan

## 1. Project Goal

Build **LeSauveur**, a Python + PyQt6 desktop MVP for a Green Tech hackathon.

LeSauveur is a simplified **urban electricity network digital twin and stress-analysis system**.

The system should simulate a fictional city's electrical infrastructure and answer:

> **What happens to the electrical network when demand or infrastructure stress increases?**

The MVP must be able to:

- represent an electrical network;
- map substations, generators, consumers, and power lines;
- simulate electricity demand;
- calculate infrastructure utilisation;
- identify weak points;
- estimate time-to-failure under sustained overload;
- simulate infrastructure failures;
- propagate load after failures;
- detect cascading failures;
- show affected consumers and critical infrastructure;
- compare hypothetical "What If?" scenarios.

### Important technical limitation

This is a **hackathon simulation**, not an engineering-grade power-grid simulator.

Do **not** implement real AC power-flow equations, SCADA integration, protection-system physics, transformer electromagnetic models, or other engineering-grade functionality.

Use a simplified, deterministic, explainable graph-based model.

The objective is to create a convincing MVP that demonstrates:

```text
COLLECT
   ↓
MAP
   ↓
SIMULATE
   ↓
IDENTIFY WEAK POINTS
   ↓
FAILURE
   ↓
CASCADE
   ↓
IMPACT
```

---

# 2. Core Demonstration

The entire MVP should support one strong live demonstration.

### Initial state

Show a fictional city with a functioning electrical network.

Everything should be green.

### Scenario

Activate:

```text
Summer Peak
```

Demand increases.

Infrastructure transitions:

```text
GREEN → YELLOW → ORANGE → RED
```

LeSauveur identifies overloaded infrastructure.

Example:

```text
SUBSTATION 04

Capacity:       120 MW
Current Load:   108 MW
Utilisation:    90%

Status:         CRITICAL
Estimated Risk: HIGH
```

### Failure

Start the simulation.

An overloaded component eventually fails.

The network recalculates.

Its load is redistributed.

Other infrastructure becomes overloaded.

Additional failures can occur.

### Final result

Show:

```text
CASCADE DETECTED

Failed Assets:       7
Affected Consumers:  31,204
Critical Assets:     3

Critical Infrastructure:
- Hospital 01
- Water Pump 03
- Industrial District
```

The system must make the chain of events visually obvious.

---

# 3. Technology Stack

Use:

- Python 3.11+
- PyQt6
- NetworkX
- NumPy
- pytest
- JSON

Optional:

- Matplotlib
- Shapely

Do NOT introduce:

- Django
- FastAPI
- React
- PostgreSQL
- Docker
- microservices
- cloud infrastructure
- authentication
- mobile application

The MVP must run locally with:

```bash
python main.py
```

---

# 4. Project Structure

Create the following architecture:

```text
lesauveur/
│
├── main.py
│
├── app/
│   ├── __init__.py
│   ├── main_window.py
│   ├── map_view.py
│   ├── control_panel.py
│   ├── statistics_panel.py
│   ├── event_log.py
│   └── styles.py
│
├── simulation/
│   ├── __init__.py
│   ├── engine.py
│   ├── network.py
│   ├── power_flow.py
│   ├── failure_model.py
│   ├── cascade.py
│   ├── scenarios.py
│   └── metrics.py
│
├── models/
│   ├── __init__.py
│   ├── substation.py
│   ├── consumer.py
│   ├── generator.py
│   ├── power_line.py
│   ├── city.py
│   └── events.py
│
├── visualization/
│   ├── __init__.py
│   ├── network_renderer.py
│   ├── heatmap.py
│   └── charts.py
│
├── data/
│   ├── city.json
│   └── scenarios.json
│
└── tests/
    ├── test_models.py
    ├── test_network.py
    ├── test_power_flow.py
    ├── test_failures.py
    ├── test_cascade.py
    └── test_scenarios.py
```

Keep simulation logic completely independent from the PyQt UI.

---

# 5. Data Models

Use Python dataclasses where appropriate.

## Generator

```python
class Generator:
    id: str
    name: str

    x: float
    y: float

    capacity_mw: float
    current_output_mw: float

    operational: bool
```

A generator provides electricity to the network.

---

## Substation

```python
class Substation:
    id: str
    name: str

    x: float
    y: float

    max_capacity_mw: float
    current_load_mw: float

    operational: bool

    damage: float
    failure_limit: float
```

Substations are the primary infrastructure that should be monitored for overload.

---

## Consumer

Consumers represent aggregated city zones rather than individual buildings.

```python
class Consumer:
    id: str
    name: str

    x: float
    y: float

    base_demand_mw: float
    current_demand_mw: float

    priority: str
```

Allowed priorities:

```text
CRITICAL
HIGH
NORMAL
LOW
```

Examples:

```text
Hospital              → CRITICAL
Water Pump             → CRITICAL
Airport                → HIGH
Industrial Zone        → HIGH
Commercial District    → NORMAL
Residential District   → NORMAL
```

---

## PowerLine

```python
class PowerLine:
    id: str

    from_node: str
    to_node: str

    max_capacity_mw: float
    current_load_mw: float

    length_km: float

    operational: bool

    damage: float
    failure_limit: float
```

---

## City

```python
class City:
    name: str

    generators: list[Generator]
    substations: list[Substation]
    consumers: list[Consumer]
    power_lines: list[PowerLine]
```

Implement:

```python
City.from_json(...)
City.to_json(...)
```

Malformed input must be handled gracefully.

---

# 6. Network Representation

Use NetworkX.

```python
network = nx.Graph()
```

### Nodes

Nodes represent:

- generators;
- substations;
- consumers.

Each node should store relevant model information.

### Edges

Edges represent power lines.

Each edge must contain:

```text
capacity
current_load
length
operational
damage
failure_limit
```

Implement functionality to:

- build the graph from a City;
- rebuild the graph after failures;
- remove failed infrastructure;
- detect disconnected consumers;
- find operational paths;
- identify isolated consumers.

---

# 7. Simplified Power Flow

Do NOT implement real AC power flow.

Implement a simplified graph-based electricity distribution model.

The model only needs to answer:

> How much simulated electrical load is passing through each infrastructure component?

Every simulation tick:

### Step 1 — Calculate demand

```python
total_demand = sum(
    consumer.current_demand_mw
    for consumer in operational_consumers
)
```

### Step 2 — Calculate available generation

```python
available_generation = sum(
    generator.capacity_mw
    for generator in operational_generators
)
```

### Step 3 — Distribute demand

Use operational paths between generators and consumers.

Prefer shorter / lower-load paths where possible.

Distribute demand across available paths.

### Step 4 — Calculate utilisation

For every power line:

```python
utilisation = current_load_mw / max_capacity_mw
```

For every substation:

```python
utilisation = current_load_mw / max_capacity_mw
```

The algorithm must be deterministic.

---

# 8. Infrastructure Status

Use the following thresholds:

```text
< 70%        NORMAL
70–85%       WARNING
85–100%      HIGH
100–120%     CRITICAL
> 120%       FAILURE_RISK
```

Create centralized functions:

```python
get_status(utilisation)
get_status_color(status)
```

Do not duplicate thresholds throughout the project.

The UI should visually communicate:

```text
NORMAL
WARNING
HIGH
CRITICAL
FAILURE
```

---

# 9. Failure Model

Overloaded infrastructure accumulates damage.

For utilisation <= 100%:

```text
damage_rate = 0
```

For utilisation > 100%:

```text
damage_rate = function_of_overload
```

A simple deterministic model is preferred.

Example:

```python
overload = max(0.0, utilisation - 1.0)

damage_rate = overload * DAMAGE_MULTIPLIER
```

Every simulation tick:

```python
damage += damage_rate * delta_time
```

When:

```python
damage >= failure_limit
```

the component fails.

Implement:

```python
calculate_damage_rate()
update_damage()
estimate_time_to_failure()
fail_component()
```

---

# 10. Time-to-Failure

For overloaded components calculate:

```text
remaining_damage = failure_limit - damage

time_to_failure =
    remaining_damage / damage_rate
```

If the component is not overloaded:

```text
time_to_failure = None
```

The UI should display:

```text
SAFE
```

or:

```text
ESTIMATED FAILURE
02m 31s
```

Always describe this internally as a **simulation estimate**.

Do not imply engineering-grade prediction.

---

# 11. Cascade Failure

This is the most important simulation feature.

When infrastructure fails:

1. mark it as non-operational;
2. remove it from the operational network;
3. recalculate power flow;
4. redistribute the affected load;
5. calculate new utilisation;
6. update damage;
7. detect new failures;
8. repeat until the system stabilizes.

Conceptually:

```text
FAILURE
   ↓
NETWORK TOPOLOGY CHANGES
   ↓
LOAD REDISTRIBUTION
   ↓
HIGHER UTILISATION
   ↓
OVERLOAD
   ↓
SECONDARY FAILURE
   ↓
LOAD REDISTRIBUTION
   ↓
CASCADE
```

Implement:

```python
run_cascade()
```

The cascade should terminate when:

```text
no new failures occur
```

or:

```text
maximum cascade iterations reached
```

to prevent infinite loops.

---

# 12. Cascade Events

Create an event model.

```python
class CascadeEvent:
    timestamp: float
    component_id: str
    component_type: str

    previous_load_mw: float
    utilisation: float

    reason: str

    affected_consumers: list[str]
```

Store events in chronological order.

The event log must be able to display them.

Example:

```text
20:42:01
Summer Peak activated

20:42:10
Substation 04 reached 100%

20:42:34
Substation 04 overloaded

20:42:58
Substation 04 FAILED

20:43:01
Load redistributed

20:43:06
Power Line 17 overloaded

20:43:11
Cascade detected
```

---

# 13. Scenario Engine

Implement predefined scenarios.

## Normal Day

```text
Demand multiplier: 1.00
```

## Summer Peak

```text
Demand multiplier: 1.35
```

## Heatwave

```text
Demand multiplier: 1.60
```

## Industrial Surge

```text
Industrial demand multiplier: 1.80
```

## Substation Failure

A selected substation becomes unavailable.

## Generator Failure

A selected generator becomes unavailable.

## Custom

Allow the user to control demand and generation parameters.

Create:

```python
Scenario
ScenarioEngine
```

Scenario definitions should be stored separately from UI code.

---

# 14. Synthetic City

Do NOT claim the network represents the real Armenian electrical grid.

Create a fictional urban network inspired by a dense Armenian city.

The dataset should contain approximately:

```text
3–5 generators
8–15 substations
20–40 consumer zones
20–50 power lines
```

Include different consumer types:

```text
Residential
Commercial
Industrial
Hospital
Water Pump
Airport
Public Infrastructure
```

Use realistic-looking but entirely synthetic MW values.

The purpose is to demonstrate the system, not to make unsupported claims about real infrastructure.

---

# 15. PyQt UI

Use a dark, professional control-room style interface.

Main layout:

```text
┌─────────────────────────────────────────────────────────────┐
│ LeSauveur     Generation 742 MW    Demand 681 MW    81%     │
├──────────────┬────────────────────────────────┬─────────────┤
│              │                                │             │
│   CONTROLS   │        CITY NETWORK            │  NETWORK    │
│              │                                │  STATUS     │
│ Scenario     │       ●──────●                 │             │
│ [Summer ▼]   │      /        \                │ Critical: 4 │
│              │     ●          ●               │ Failed: 0   │
│ [START]      │    / \        /                │             │
│ [PAUSE]      │   ●   ●──────●                 │             │
│ [RESET]      │                                │             │
│ [WHAT IF?]   │                                │             │
│              │                                │             │
├──────────────┴────────────────────────────────┴─────────────┤
│ EVENT LOG                                                     │
└─────────────────────────────────────────────────────────────┘
```

---

# 16. Map View

The central map should display:

- generators;
- substations;
- consumers;
- power lines.

Use fixed coordinates from the synthetic city dataset.

Do not depend on an external map service for the MVP.

Power lines should visually communicate their utilisation.

Nodes should visually communicate their status.

Clicking an asset opens detailed information.

---

# 17. Asset Inspector

When the user clicks a substation:

```text
SUBSTATION 04

Capacity:       120 MW
Current Load:   108 MW
Utilisation:    90%

Status:         CRITICAL

Damage:         42%

Estimated Failure:
01:42

Connected Consumers:
2,418

Critical Consumers:
3
```

For a power line:

```text
POWER LINE 17

Capacity:       50 MW
Current Flow:   47 MW
Utilisation:    94%

Status:         CRITICAL
```

The inspector must update dynamically.

---

# 18. KPI Dashboard

Always show:

```text
NETWORK STATUS

Generation
742 MW

Demand
681 MW

Network Utilisation
81%

Operational Assets
42 / 45

Critical Assets
4

Affected Consumers
0

Cascade Risk
LOW
```

After a severe scenario:

```text
NETWORK STATUS

Generation
742 MW

Demand
1,024 MW

Network Utilisation
117%

Operational Assets
35 / 45

Critical Assets
12

Affected Consumers
31,204

Cascade Risk
CRITICAL
```

---

# 19. Top Vulnerability Panel

Add:

```text
TOP 5 VULNERABLE ASSETS
```

Example:

```text
1. Substation 04
   118%
   Estimated failure: 00:48

2. Power Line 17
   111%
   Estimated failure: 01:21

3. Substation 02
   103%
   Estimated failure: 02:14
```

Sort assets by a consistent risk metric.

Do not use arbitrary hard-coded rankings.

---

# 20. Vulnerability Map

Add a button:

```text
VULNERABILITY MAP
```

This should emphasize infrastructure risk rather than ordinary network topology.

The city should visually expose hotspots.

The user should immediately see where the network is under stress.

---

# 21. Simulation Controls

Required controls:

```text
[ START ]
[ PAUSE ]
[ RESET ]

[ SPEED ×1 ]
[ SPEED ×10 ]
[ SPEED ×100 ]

[ SIMULATE ]

[ WHAT IF? ]

[ VULNERABILITY MAP ]
```

Scenario selector:

```text
Scenario:
[ Normal Day ▼ ]
```

Optional controls:

```text
Demand       ███████░░░ 75%
Generation   █████████░ 90%
Temperature  ████████░░ 38°C
```

The UI must never block the Qt event loop.

Use QTimer or appropriate background processing for simulation ticks.

---

# 22. What-If Analysis

Implement a dedicated hypothetical scenario mode.

The user should be able to select:

```text
What happens if:

☑ Substation 04 fails
☐ Generator 02 fails
☐ Power Line 17 fails
☐ Industrial demand +30%
☐ Heatwave +20%
```

Run the scenario on a copy of the network state.

The actual current state must remain unchanged.

Display:

```text
PROJECTED IMPACT

Failed Assets:       5
Affected Consumers:  31,204
Affected Lines:      8
Affected Substations: 4

Critical Infrastructure:
- Hospital 01
- Water Pump 03

Cascade Risk:
HIGH
```

---

# 23. Import / Export

Support JSON import/export.

Required:

```text
[ IMPORT CITY ]
[ EXPORT CITY ]
```

Example:

```json
{
  "name": "LeSauveur Demo City",
  "generators": [],
  "substations": [],
  "consumers": [],
  "power_lines": []
}
```

This supports the challenge's infrastructure-data aspect.

---

# 24. Simulation Engine API

The UI should interact with a single high-level engine.

Example:

```python
class SimulationEngine:

    def load_city(self, city: City) -> None:
        ...

    def reset(self) -> None:
        ...

    def tick(self, delta_time: float) -> None:
        ...

    def run_scenario(self, scenario: Scenario) -> None:
        ...

    def calculate_power_flow(self) -> None:
        ...

    def update_damage(self, delta_time: float) -> None:
        ...

    def run_cascade(self) -> list[CascadeEvent]:
        ...

    def get_metrics(self) -> SimulationMetrics:
        ...

    def get_vulnerable_assets(self) -> list:
        ...

    def simulate_what_if(self, scenario: Scenario):
        ...
```

Do not expose low-level implementation details directly to UI widgets.

---

# 25. Simulation Metrics

Create a centralized metrics model.

It should contain:

```text
total_generation_mw
total_demand_mw
network_utilisation
operational_assets
total_assets
critical_assets
failed_assets
affected_consumers
critical_consumers_affected
cascade_risk
```

This object feeds the KPI dashboard.

---

# 26. Testing

Create automated tests with pytest.

Test:

### Models

- serialization;
- deserialization;
- validation;
- default values.

### Network

- graph construction;
- nodes;
- edges;
- failed component removal;
- disconnected consumers.

### Power Flow

- normal demand;
- high demand;
- insufficient generation;
- overloaded line;
- overloaded substation.

### Failure

- no damage under normal load;
- damage under overload;
- time-to-failure;
- component failure.

### Cascade

- primary failure;
- load redistribution;
- secondary overload;
- secondary failure;
- cascade termination.

### Scenarios

- Normal Day;
- Summer Peak;
- Heatwave;
- Industrial Surge;
- Substation Failure;
- Generator Failure;
- Custom scenario.

---

# 27. Development Phases

Implement strictly in this order.

## PHASE 1 — Models

Implement:

```text
Generator
Substation
Consumer
PowerLine
City
CascadeEvent
```

Add JSON serialization.

Write tests.

Do not build the UI yet.

---

## PHASE 2 — Network Engine

Implement:

```text
NetworkX graph
graph construction
operational topology
path finding
failure removal
disconnected consumer detection
```

Write tests.

---

## PHASE 3 — Power Flow

Implement:

```text
demand calculation
generation calculation
load distribution
line utilisation
substation utilisation
status calculation
```

Write tests.

---

## PHASE 4 — Failure Model

Implement:

```text
stress
damage
damage rate
time-to-failure
component failure
```

Write tests.

---

## PHASE 5 — Cascade

Implement:

```text
failure
↓
network update
↓
load redistribution
↓
overload
↓
secondary failure
```

Write tests.

This is the most important backend milestone.

---

## PHASE 6 — Scenarios

Implement:

```text
Normal Day
Summer Peak
Heatwave
Industrial Surge
Substation Failure
Generator Failure
Custom
```

Write tests.

---

## PHASE 7 — PyQt UI

Implement:

```text
MainWindow
MapView
ControlPanel
StatisticsPanel
EventLog
```

Connect them to SimulationEngine.

---

## PHASE 8 — Visualisation

Implement:

```text
network rendering
status rendering
asset selection
heatmap
vulnerability visualization
charts
animations
```

---

## PHASE 9 — What-If Analysis

Implement:

```text
scenario cloning
hypothetical failure
hypothetical demand increase
impact analysis
```

---

## PHASE 10 — Pitch Polish

Implement:

```text
professional dark UI
smooth simulation
clear status indicators
event timeline
KPI dashboard
vulnerability ranking
```

Do not add new major backend features at this stage.

---

# 28. Coding Rules for GitHub Copilot

Follow these rules throughout implementation:

1. Use Python type hints.
2. Use dataclasses where appropriate.
3. Keep simulation logic independent from PyQt.
4. Never put business logic directly inside UI widgets.
5. Avoid global mutable state.
6. Keep functions small and testable.
7. Use descriptive names.
8. Add docstrings to public classes and functions.
9. Centralize configuration and thresholds.
10. Do not duplicate constants.
11. Handle malformed JSON gracefully.
12. Do not introduce unnecessary dependencies.
13. Keep the UI responsive.
14. Never block the Qt event loop.
15. Use QTimer or background processing where appropriate.
16. Write tests for every major simulation feature.
17. Do not rewrite working modules unnecessarily.
18. Do not implement future phases early.
19. Do not add fake AI functionality unless explicitly requested.
20. Prefer deterministic behaviour over random behaviour for the core demo.
21. Make simulation results explainable.
22. Keep the application runnable with `python main.py`.

---

# 29. Definition of Done

The MVP is complete when this exact workflow works:

```text
1. Launch LeSauveur.

2. Synthetic city network appears.

3. All infrastructure is operational.

4. Network is mostly green.

5. Select "Summer Peak".

6. Demand increases.

7. Infrastructure changes:
   green → yellow → orange → red.

8. Vulnerable assets appear in the risk panel.

9. Time-to-failure estimates appear.

10. Press SIMULATE.

11. An overloaded component fails.

12. Network topology updates.

13. Load is redistributed.

14. Other components become overloaded.

15. Secondary failures occur.

16. Event log records the cascade.

17. Affected consumers increase.

18. Critical infrastructure is highlighted.

19. Final dashboard shows:
    - failed assets
    - affected consumers
    - critical infrastructure
    - cascade duration
    - highest-risk assets

20. Press RESET.

21. Network returns to its initial state.

22. Run another scenario successfully.
```

---

# 30. Product Positioning

The product should be described as:

> **LeSauveur is a digital-twin prototype for urban electricity networks that visualizes infrastructure, simulates stress scenarios, identifies vulnerable assets, and models cascading failures before they happen.**

Short version:

> **Don't wait for the blackout. Simulate it first.**

The system should demonstrate:

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

---

# 31. Critical MVP Principle

Do not optimize for technical complexity.

Optimize for:

**clarity + simulation + visual impact + explainability.**

A judge should understand the product within 10 seconds.

The intended visual story is:

```text
NORMAL CITY
     ↓
HIGH DEMAND
     ↓
NETWORK STRESS
     ↓
WEAK POINT IDENTIFIED
     ↓
FAILURE
     ↓
LOAD REDISTRIBUTION
     ↓
CASCADE
     ↓
REAL-WORLD IMPACT
```

---

# 32. First Copilot Task

Do NOT implement the entire project at once.

Start with **PHASE 1 only**.

After completing Phase 1:

1. Show all files created.
2. Show the public interfaces of the models.
3. Run all Phase 1 tests.
4. Report test results.
5. Fix any failures.
6. Stop and wait for the next phase.

Do not proceed to Phase 2 automatically.
