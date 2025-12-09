# PROSIM Technical Documentation

This document provides technical details about the PROSIM simulation algorithms, API reference, and configuration guide.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Simulation Algorithms](#simulation-algorithms)
3. [API Reference](#api-reference)
4. [Configuration Guide](#configuration-guide)
5. [File Formats](#file-formats)

---

## Architecture Overview

### Module Structure

```
prosim/
├── models/          # Pydantic data models
│   ├── company.py   # Company and GameState
│   ├── decisions.py # Weekly decision input
│   ├── inventory.py # Inventory tracking
│   ├── machines.py  # Machine definitions
│   ├── operators.py # Workforce management
│   ├── orders.py    # Order tracking
│   └── report.py    # Weekly reports
│
├── engine/          # Simulation logic
│   ├── simulation.py   # Main orchestrator
│   ├── production.py   # Production calculations
│   ├── costs.py        # Cost calculations
│   ├── demand.py       # Demand generation
│   ├── inventory.py    # Inventory management
│   ├── workforce.py    # Operator management
│   ├── validation.py   # Decision validation
│   └── calibration.py  # Parameter calibration
│
├── io/              # File I/O
│   ├── decs_parser.py  # DECS file parsing
│   ├── rept_parser.py  # REPT file parsing
│   └── state_io.py     # Save/load game state
│
├── config/          # Configuration
│   └── schema.py       # Pydantic config models
│
├── cli/             # Command-line interface
│   └── main.py         # Click CLI
│
└── i18n/            # Internationalization
    └── locales/        # Translation files
```

### Data Flow

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│  Decisions   │────►│   Simulation    │────►│    Report    │
│  (DECS)      │     │    Engine       │     │    (REPT)    │
└──────────────┘     └─────────────────┘     └──────────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │  Company State  │
                   │  - Inventory    │
                   │  - Workforce    │
                   │  - Machines     │
                   │  - Costs        │
                   └─────────────────┘
```

---

## Simulation Algorithms

### 1. Week Processing Flow

The `Simulation.process_week()` method orchestrates all weekly calculations:

```python
def process_week(company, decisions) -> SimulationWeekResult:
    # 1. Apply decisions to machine floor
    machine_floor = apply_decisions(decisions)

    # 2. Process workforce (training, scheduling, efficiency)
    workforce, efficiency_results = process_workforce(decisions)

    # 3. Receive pending orders
    inventory = receive_orders(company.orders)

    # 4. Calculate production
    production_result = calculate_production(machine_floor, efficiency_results)

    # 5. Update inventory with production
    inventory = apply_production(inventory, production_result)

    # 6. Handle shipping (if shipping week)
    if is_shipping_week(week):
        inventory, demand_result = process_shipping(inventory, demand)

    # 7. Calculate costs
    cost_report = calculate_costs(production, inventory, workforce)

    # 8. Generate report
    return SimulationWeekResult(report, updated_company)
```

### 2. Production Algorithm

**Location**: `prosim/engine/production.py`

The production formula calculates net output through several stages:

```
Productive Hours = (Scheduled Hours - Setup Time) × Operator Efficiency
Gross Production = Productive Hours × Production Rate
Rejects = Gross Production × Reject Rate
Net Production = Gross Production - Rejects
```

**Implementation details:**

```python
class ProductionEngine:
    def calculate_machine_production(self, input: ProductionInput) -> MachineProductionResult:
        # Step 1: Calculate setup time (when part type changes)
        setup_hours = self.calculate_setup_time(machine, new_part_type)

        # Step 2: Calculate available hours after setup
        available_hours = max(0.0, scheduled_hours - setup_hours)

        # Step 3: Apply operator efficiency
        productive_hours = available_hours * operator_efficiency

        # Step 4: Calculate gross production
        production_rate = self.get_production_rate(part_type, department)
        gross_production = productive_hours * production_rate

        # Step 5: Apply reject rate
        reject_rate = self.config.production.reject_rate  # Default: 17.8%
        rejects = gross_production * reject_rate
        net_production = gross_production - rejects

        return MachineProductionResult(...)
```

**Production Rates:**

| Department | Type | Rate (units/hr) |
|------------|------|-----------------|
| Parts | X' | 60 |
| Parts | Y' | 50 |
| Parts | Z' | 40 |
| Assembly | X | 40 |
| Assembly | Y | 30 |
| Assembly | Z | 20 |

**Setup Time:**
- Incurred when machine switches to different part type
- Default: 2 hours (configurable per department)
- No setup time when continuing same part type

### 3. Operator Efficiency Algorithm

**Location**: `prosim/engine/workforce.py`

Operator efficiency varies based on training status:

```python
class OperatorManager:
    def calculate_efficiency(self, operator: Operator) -> OperatorEfficiencyResult:
        if operator.training_status == TrainingStatus.IN_TRAINING:
            return OperatorEfficiencyResult(efficiency=0.0, reason="in_training")

        if operator.is_trained:
            # Trained: 95-100% efficiency (random)
            efficiency = random.uniform(
                self.config.workforce.efficiency.trained_min,  # 0.95
                self.config.workforce.efficiency.trained_max,  # 1.00
            )
        else:
            # Untrained: 60-90% efficiency (random)
            efficiency = random.uniform(
                self.config.workforce.efficiency.untrained_min,  # 0.60
                self.config.workforce.efficiency.untrained_max,  # 0.90
            )

        return OperatorEfficiencyResult(efficiency=efficiency)
```

### 4. Cost Calculation Algorithm

**Location**: `prosim/engine/costs.py`

Costs are calculated in two categories:

#### Per-Product Costs (X, Y, Z)

| Category | Formula |
|----------|---------|
| Labor | `productive_hours × $10/hr` |
| Machine Setup | `setup_hours × $40/hr` |
| Machine Repair | `repair_count × $400` |
| Raw Materials | `gross_production × RM_cost` |
| Purchased Parts | `parts_received × part_cost` |
| Equipment Usage | `productive_hours × equip_rate` |
| Parts Carrying | `ending_inventory × $0.05/unit` |
| Products Carrying | `ending_inventory × $0.10/unit` |
| Demand Penalty | `unfulfilled × $10/unit` |

#### Overhead Costs

| Category | Formula |
|----------|---------|
| Quality Planning | Decision input |
| Plant Maintenance | Decision input |
| Training Cost | `operators_trained × $1,000` |
| Hiring Cost | `new_hires × $2,700` |
| Layoff Cost | `weeks_unscheduled × $200` |
| Termination Cost | `terminated × $400` |
| RM Carrying | `ending_RM × $0.01/unit` |
| Ordering Cost | `orders × $100 + expedited × $1,200` |
| Fixed Expense | `$1,500/week` |

### 5. Demand Generation Algorithm

**Location**: `prosim/engine/demand.py`

Demand follows a forecasting model with decreasing uncertainty:

```python
class DemandManager:
    def generate_forecast(self, product: str, weeks_until_shipping: int) -> DemandForecast:
        base_demand = self.config.demand.base_demand[product]  # X=600, Y=400, Z=200
        std_dev = self.config.demand.forecast_std_dev_weeks_out[weeks_until_shipping]

        # Generate actual demand (revealed at shipping)
        actual = max(0, int(random.gauss(base_demand, std_dev)))

        return DemandForecast(
            product=product,
            forecast_mean=base_demand,
            forecast_std_dev=std_dev,
            actual_demand=actual,  # Only revealed at shipping
        )
```

**Uncertainty by weeks until shipping:**

| Weeks Out | Std Dev |
|-----------|---------|
| 4 | 300 |
| 3 | 300 |
| 2 | 200 |
| 1 | 100 |
| 0 (shipping) | 0 (exact) |

### 6. Machine Repair Algorithm

**Location**: `prosim/engine/simulation.py`

Machine breakdowns are stochastic events:

```python
def generate_machine_repairs(self) -> dict[str, int]:
    repairs = {"X": 0, "Y": 0, "Z": 0}
    probability = self.config.equipment.repair.probability_per_machine_per_week  # 10%

    for machine in self.machine_floor.machines.values():
        if random.random() < probability:
            # Machine broke down - attribute to current product type
            product_type = machine.assignment.part_type.replace("'", "")
            repairs[product_type] += 1

    return repairs
```

### 7. Inventory Management Algorithm

**Location**: `prosim/engine/inventory.py`

Inventory flow follows this sequence each week:

```python
class InventoryManager:
    def process_week(self, inventory, orders, production, demand) -> Inventory:
        # 1. Receive orders that are due this week
        inventory = self.receive_due_orders(inventory, orders, current_week)

        # 2. Consume raw materials for parts production
        inventory = self.consume_raw_materials(inventory, parts_production)

        # 3. Add parts production to inventory
        inventory = self.add_parts_production(inventory, parts_production)

        # 4. Consume parts for assembly
        inventory = self.consume_parts(inventory, assembly_production)

        # 5. Add assembly production to inventory
        inventory = self.add_products_production(inventory, assembly_production)

        # 6. Fulfill demand (on shipping weeks)
        if is_shipping_week:
            inventory = self.fulfill_demand(inventory, demand)

        return inventory
```

---

## API Reference

### Simulation Class

```python
from prosim.engine.simulation import Simulation
from prosim.config.schema import ProsimConfig

# Create simulation with default config
simulation = Simulation()

# Create with custom config and seed
simulation = Simulation(config=custom_config, random_seed=42)

# Process a week
result = simulation.process_week(company, decisions)
# Returns: SimulationWeekResult

# Access result attributes
result.weekly_report     # WeeklyReport
result.updated_company   # Company
result.production_result # ProductionResult
result.cost_report       # WeeklyCostReport
```

### Company Model

```python
from prosim.models.company import Company, GameState

# Create game state
game_state = GameState.create_single_player(
    game_id="abc123",
    company_name="My Company",
    max_weeks=15,
    random_seed=42,
)

# Get company
company = game_state.get_company(company_id=1)

# Access company state
company.current_week        # int
company.inventory           # Inventory
company.workforce           # Workforce
company.machine_floor       # MachineFloor
company.order_book          # OrderBook
company.total_costs         # float
company.latest_report       # WeeklyReport | None
```

### Decisions Model

```python
from prosim.models.decisions import Decisions, MachineDecision, PartOrders

decisions = Decisions(
    week=1,
    company_id=1,
    quality_budget=750.0,
    maintenance_budget=500.0,
    raw_materials_regular=10000.0,
    raw_materials_expedited=0.0,
    part_orders=PartOrders(x_prime=500.0, y_prime=400.0, z_prime=300.0),
    machine_decisions=[
        MachineDecision(machine_id=1, part_type=1, scheduled_hours=40.0),
        MachineDecision(machine_id=2, part_type=2, scheduled_hours=40.0),
        # ... more machines
    ],
)
```

### Configuration API

```python
from prosim.config.schema import ProsimConfig, get_default_config

# Get default config
config = get_default_config()

# Create from dictionary
config = ProsimConfig.from_dict({
    "production": {"reject_rate": 0.15},
    "workforce": {"efficiency": {"trained_min": 0.97}},
})

# Load from file
config = ProsimConfig.from_file("config.json")

# Save to file
config.to_file("config.yaml")

# Merge overrides
new_config = config.merge({"production": {"reject_rate": 0.12}})
```

### File I/O API

```python
from prosim.io import (
    parse_decs,
    write_decs,
    parse_rept,
    write_rept,
    write_rept_human_readable,
    save_game,
    load_game,
    list_saves,
)

# Parse DECS file
decisions = parse_decs("DECS14.DAT")

# Write DECS file
write_decs(decisions, "output.DAT")

# Parse REPT file
report = parse_rept("REPT14.DAT")

# Write human-readable report
text = write_rept_human_readable(report)

# Save/load game state
save_game(game_state, slot=1, save_name="Week 5")
saved = load_game(slot=1)
game_state = saved.game_state
```

---

## Configuration Guide

### Configuration Structure

The `ProsimConfig` class contains nested configuration sections:

```yaml
production:
  parts_rates: {X': 60, Y': 50, Z': 40}
  assembly_rates: {X: 40, Y: 30, Z: 20}
  reject_rate: 0.178
  bom: {X: {X': 1}, Y: {Y': 1}, Z: {Z': 1}}
  raw_materials_per_part: {X': 1.0, Y': 1.0, Z': 1.0}
  setup_time: {parts_department: 2.0, assembly_department: 2.0}

logistics:
  lead_times:
    raw_materials_regular: 3
    raw_materials_expedited: 1
    purchased_parts: 1
  expedited_shipping_cost: 1200.0

workforce:
  efficiency:
    trained_min: 0.95
    trained_max: 1.00
    untrained_min: 0.60
    untrained_max: 0.90
  costs:
    hiring_cost: 2700.0
    layoff_cost_per_week: 200.0
    termination_cost: 400.0
    training_cost_per_worker: 1000.0

equipment:
  repair:
    probability_per_machine_per_week: 0.10
    cost_per_repair: 400.0
  rates:
    parts_department: 100.0
    assembly_department: 80.0

costs:
  fixed:
    fixed_expense_per_week: 1500.0
  carrying:
    raw_materials: 0.01
    parts: 0.05
    products: 0.10
  labor:
    regular_hourly: 10.0
    overtime_multiplier: 1.5

demand:
  forecast_std_dev_weeks_out: {4: 300, 3: 300, 2: 200, 1: 100, 0: 0}

simulation:
  parts_machines: 4
  assembly_machines: 5
  max_scheduled_hours: 50.0
  regular_hours: 40.0
  shipping_frequency: 4
  random_seed: null
```

### Parameter Sources

Parameters are marked as **verified** or **estimated**:

| Parameter | Status | Source |
|-----------|--------|--------|
| Production rates | Verified | Case study, REPT files |
| Reject rate | Verified | 17.8% from REPT14 |
| Lead times | Verified | Course materials |
| Hiring cost ($2,700) | Verified | week1.txt |
| Layoff cost ($200) | Verified | week1.txt |
| Termination cost ($400) | Verified | week1.txt |
| Fixed expense ($1,500) | Verified | week1.txt |
| Repair cost ($400) | Verified | week1.txt |
| Labor rate ($10/hr) | Verified | PPT materials |
| Setup time (2 hrs) | Estimated | - |
| Carrying costs | Estimated | - |
| Training cost ($1,000) | Estimated | - |
| Machine repair probability | Estimated | 10-15% |
| Operator efficiency ranges | Estimated | Observed ranges |

### Customizing Configuration

**Example: Creating a difficulty variant**

```python
# Easy mode - lower reject rate, more efficient workers
easy_config = ProsimConfig.from_dict({
    "production": {"reject_rate": 0.10},
    "workforce": {
        "efficiency": {
            "trained_min": 0.98,
            "untrained_min": 0.75,
        }
    },
    "equipment": {
        "repair": {"probability_per_machine_per_week": 0.05}
    },
})

# Hard mode - higher reject rate, less efficient workers
hard_config = ProsimConfig.from_dict({
    "production": {"reject_rate": 0.25},
    "workforce": {
        "efficiency": {
            "trained_max": 0.95,
            "untrained_max": 0.75,
        }
    },
    "equipment": {
        "repair": {"probability_per_machine_per_week": 0.20}
    },
})
```

---

## File Formats

### DECS File Format

Decision files contain weekly player decisions:

```
Line 1: [Week] [Company#] [QualityBudget] [MaintBudget] [RMOrderReg] [RMOrderExp]
Line 2: [PartOrderX'] [PartOrderY'] [PartOrderZ']
Lines 3-11: [MachineID] [TrainFlag] [PartType] [Hours]
```

**Example (DECS14.DAT):**
```
14            2             750           500           10000         10000
 600           500           400
 3             1             1             40
 5             1             2             40
 2             1             1             40
 7             1             1             40
 4             1             1             50
 6             1             2             50
 1             1             1             50
 26            1             2             50
 18            1             2             20
```

**Field definitions:**
- `TrainFlag`: 0 = send for training, 1 = working normally
- `PartType`: 1 = X/X', 2 = Y/Y', 3 = Z/Z'
- `Hours`: 0-50 scheduled hours

### REPT File Format

Report files contain simulation results:

```
Line 1:     [Week] [Company] [Unknown] [Unknown] [Unknown]
Lines 2-11: Cost data by product (X, Y, Z, Total) × 2 (weekly, cumulative)
Line 12:    [WeeklyTotal] [CumulativeTotal]
Lines 13-14: Overhead costs breakdown (weekly, cumulative)
Lines 15-23: Production data per machine
Line 24:    Raw materials inventory
Lines 25-31: Pending orders
Lines 32-37: Parts and products inventory
Lines 38-40: Demand estimates
Lines 41-42: Performance metrics
```

### Save File Format

Game state is saved as JSON:

```json
{
  "version": "1.0.0",
  "metadata": {
    "save_id": "abc123",
    "save_name": "Week 5",
    "created_at": "2024-12-09T10:30:00Z",
    "updated_at": "2024-12-09T12:45:00Z",
    "game_id": "xyz789",
    "company_name": "My Company",
    "current_week": 5,
    "total_costs": 45000.0,
    "save_slot": 1
  },
  "game_state": {
    "game_id": "xyz789",
    "mode": "single_player",
    "current_week": 5,
    "max_weeks": 15,
    "random_seed": 42,
    "companies": [
      {
        "company_id": 1,
        "name": "My Company",
        "inventory": { ... },
        "workforce": { ... },
        "machine_floor": { ... },
        "order_book": { ... }
      }
    ]
  },
  "config": { ... }
}
```

---

## Appendix: Calibration Data

See [calibration_report.md](calibration_report.md) for detailed calibration findings from comparing the simulation against original REPT files.

Key findings:
- Production rates match documentation exactly
- Reject rate varies 11.85% - 17.8% (influenced by quality budget)
- Operator efficiency ranges: trained 95-100%, untrained 58-90%
- All verified cost constants match original files

---

*This documentation is part of the PROSIM Reconstruction Project. For player documentation, see [game_manual.md](game_manual.md).*
