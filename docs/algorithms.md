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

**Location**: `prosim/engine/workforce.py`, `prosim/config/defaults.py`

#### Verified Two-Component Model (Dec 2025)

Forensic analysis of `week1.txt` and XTC game state files revealed that operator output is determined by **two separate hidden stats**:

```
Output = Scheduled_Hours × Time_Efficiency × Production_Rate × Proficiency × (1 - Reject_Rate)
```

| Component | Stored In | Meaning | Range |
|-----------|-----------|---------|-------|
| **Time Efficiency** | XTC float 1 | Productive Hours ÷ Scheduled Hours | 64-103% |
| **Proficiency** | XTC float 2 | Output quality multiplier (fixed at hire) | 51-104% |

**Evidence from Week 1 report (`archive/data/week1.txt`):**
```
Operator 1: Time Eff 92.5% × Proficiency 70.1% = 64.8% combined
Operator 3: Time Eff 92.5% × Proficiency 103.7% = 95.9% combined (expert!)
Operator 5: Time Eff 100.0% × Proficiency 55.2% = 55.2% combined
```

The Training Matrix in `defaults.py` represents the **combined** efficiency (Time × Proficiency) at each training level and quality tier. The matrix was verified against XTC files with 0.2% average error.

#### Operator Efficiency Ceiling (Dec 2025)

Each operator has a **maximum efficiency ceiling** determined by their Quality Tier (Proficiency). Training improves Time Efficiency, but cannot exceed the ceiling set by Proficiency.

**Cross-game analysis of Operator 3:**
| Game Run | Proficiency | Notes |
|----------|-------------|-------|
| Andy (Week 12) | 111.9% | Expert |
| Shorty (Week 13) | 108.9% | Expert |
| Nelson (Week 14) | 106.2% | Expert |
| week1.txt | 103.7% | Expert |

Operator 3 is consistently an expert across **all** game runs (std dev 3.1%), suggesting starting operators (1-9) have **fixed profiles**:

| Operator | Profile | Ceiling |
|----------|---------|---------|
| Op 3 | Expert | ~132% |
| Op 7 | Strong | ~110% |
| Op 4 | Low | ~60% |
| Op 5 | Low | ~55% |

**Hired operators (10+)** appear to have randomized quality tiers.

#### Current Implementation (Two-Component Model)

The implementation uses the verified two-component model where efficiency is calculated from the training matrix and proficiency:

```python
class Operator:
    @property
    def efficiency(self) -> float:
        """Combined efficiency = time_efficiency × proficiency."""
        if self.is_in_training_class:
            return 0.0
        return self.time_efficiency * self.proficiency

    @property
    def time_efficiency(self) -> float:
        """Time efficiency from training matrix lookup."""
        return TRAINING_MATRIX[self.quality_tier][self.training_level] / 100.0
```

**Starting operator profiles** (fixed, verified via XTC analysis):

| Op | Quality Tier | Proficiency | Max Efficiency | Notes |
|----|--------------|-------------|----------------|-------|
| 1 | 6 | 1.039 | ~119% | Normal |
| 2 | 5 | 1.097 | ~120% | Normal |
| 3 | 9 | 1.122 | **~134%** | **EXPERT** |
| 4 | 5 | 1.093 | ~119% | Normal |
| 5 | 5 | 1.028 | ~112% | Normal |
| 6 | 9 | 0.836 | ~100% | High tier, low prof |
| 7 | 9 | 0.934 | ~112% | Below average |
| 8 | 2 | 0.850 | ~95% | Low tier |
| 9 | 2 | 0.900 | ~100% | Low tier |

#### XTC Game State File Verification (Dec 2025)

Binary analysis of `prosim.xtc` (Week 9) and `prosim1.xtc` (Week 13) validates the two-component model:

**XTC Float Format:**
- Each operator record contains two IEEE 754 floats after a `0x15` delimiter
- Float1: Proficiency (normalized by ~1.088)
- Float2: Unknown component (possibly tier-related)

**Key findings:**

1. **Float1 correlates with proficiency** (scale factor 1.088):
   ```
   XTC float1 × 1.088 ≈ Our derived proficiency

   Op 3 (EXPERT): 1.0312 × 1.088 = 1.1219 → Model: 1.122 ✓ EXACT
   Op 2:          1.0192 × 1.088 = 1.1089 → Model: 1.097 ✓
   Op 1:          0.9667 × 1.088 = 1.0518 → Model: 1.039 ✓
   Op 6:          0.6397 × 1.088 = 0.6960 → Model: 0.836 (close)
   ```

2. **Float values are IDENTICAL across Week 9 and Week 13**:
   - Confirms proficiency is fixed at hire (never changes)
   - Suggests player may not have trained operators (user hypothesis)

3. **11 unique float pairs** for 9 operators:
   - 2 extra pairs may be defaults or represent hired operators

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

### 5. Game Performance Efficiency (Distinguished from Operator Efficiency)

**Location**: Game-level metric, not directly in code

The game calculates an **overall efficiency metric** to rank company performance:

```
Game Efficiency = (Standard Costs / Actual Costs) × 100%
```

**Important distinction:**
- **Operator Efficiency**: How well an operator produces output (`Production / Expected`)
- **Game Efficiency**: How cost-effective the company operates (`Standard / Actual`)

**Interpretation:**
| Efficiency | Meaning |
|------------|---------|
| > 100% | Outperforming standard (lower actual costs) |
| = 100% | Meeting standard exactly |
| < 100% | Underperforming (higher actual costs) |

**Strategic Insight - The Shutdown Strategy:**

An advanced strategy exploits this formula during endgame:
1. Build up inventory well before shipping week
2. In final weeks, reduce scheduled hours to minimum
3. Continue shipping from inventory
4. Minimal actual costs while maintaining output = very high efficiency

This works because:
- Standard costs assume continuous production
- Actual costs drop when production stops
- If inventory is sufficient, shipping continues normally
- Result: Efficiency spikes above 100%

Evidence from Week 16 spreadsheet shows operators at 99-132% efficiency during shutdown phase with Z' Production = 0.

### 6. Demand Generation Algorithm

**Location**: `prosim/engine/demand.py`

Demand follows a forecasting model with decreasing uncertainty:

```python
class DemandManager:
    def generate_forecast(self, product: str, weeks_until_shipping: int) -> DemandForecast:
        base_demand = self.config.demand.base_demand[product]  # X=8467, Y=6973, Z=5475
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

### 7. Machine Repair Algorithm

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

### 8. Inventory Management Algorithm

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
| Reject rate formula | Verified | 17.8% at $750, floor ~1.5% at $2,500 |
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
    "created_at": "2025-12-09T10:30:00Z",
    "updated_at": "2025-12-09T12:45:00Z",
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

## Appendix A: ProsimTable.xls Spreadsheet Structure

The original reverse-engineering spreadsheet (`archive/spreadsheets/ProsimTable.xls`) was the primary tool used to analyze and predict PROSIM behavior. This section documents its structure for preservation purposes.

### Tabs Overview

| Tab | Purpose |
|-----|---------|
| `DECS14` | Decision entry (mirrors DECS file format) |
| `Week Sumary` | Weekly summary with current/last week tracking |
| `Weekly Planing` | Production planning calculations |
| `Entry` | Operator assignments and comparison data (includes Andy/Shorty data) |
| `Results` | Production predictions with daily (Mon-Fri) breakdown |
| `Eff` | Cost breakdown and efficiency calculations |
| `Operators` | Training matrix, operator tracking, efficiency lookups |
| `Forcasting` | Demand forecasting calculations |
| `Graph` | Reject rate analysis (source of logarithmic formula) |
| `Cost` | Detailed cost calculations |
| `Data` | Raw data and machine production tracking |

### External Dependencies

The spreadsheet references an external file `Nelson.xls` for DGET/DSUM database lookups. The formulas follow this pattern:

```
=DGET($A$6:$E$34,$C$6,$J21:$J22)  -- "days w/o" lookup
=DGET($A$6:$E$34,$D$6,$J21:$J22)  -- "days with" lookup
```

**Database structure required in Nelson.xls:**
- Row 6: Headers (`op`, `base`, `days_wo`, `days_with`, `op`)
- Rows 7-15: Operator data keyed by operator number in column E

### Operators Tab Structure

The Operators tab contains the **Training Matrix** (verified source for `prosim/config/defaults.py`):

**Location**: Rows 6-16, Columns K-U (headers: "not trained", "A" through "J")

| Training Level | Not Trained | A | B | C | D | E | F | G | H | I | J |
|----------------|-------------|-----|-----|-----|-----|------|------|------|------|------|------|
| 0 | 20% | 61% | 79% | 89% | 96% | 100% | 103% | 106% | 108% | 109% |
| 1 | 21% | 63% | 81% | 91% | 98% | 103% | 106% | 109% | 111% | 112% |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| 9 | 22% | 67% | 87% | 98% | 105% | 110% | 113% | 116% | 118% | 120% |

**Operator tracking section** (Rows 21-38):
- Column I: Operator number
- Column J: "Not Trained" weeks (calculated via DGET)
- Column K: "Trained" weeks (calculated via DGET)
- Column L-M: Capped values (max 9 for lookup)
- Column N: Training level lookup (A-J)
- Column O: "days w/o" (from Nelson.xls)
- Column P: "days with" (from Nelson.xls)

### Results Tab Structure

Production planning with Material Requirements Planning (MRP):

**100% Estimated Section** (Rows 2-13):
- Operator efficiency and production calculations
- Formula: `Production = Hours × Efficiency × Rate`

**Material Based Estimate Section** (Rows 15-26):
- Adjusted production based on material availability
- Prime component (X', Y', Z') inventory tracking

**Daily Breakdown** (Columns L-AJ):
- Monday through Friday production scheduling
- "Next Day" inventory projections
- Reduction percentages for material constraints

### Reconstruction Notes (December 2025)

To restore full functionality of ProsimTable.xls:

1. **Nelson.xls** was reconstructed with seed data derived from:
   - Existing values in the Operators tab (Not Trained/Trained columns)
   - Formula reverse-engineering to determine required database structure
   - Training data: Op 3=18/9, Op 7=21/9, Op 26=15/5, Op 2=20/5, Op 6=18/10, Op 4=16/5, Op 1=13/6, Op 5=16/5, Op 18=12/6

2. **Column C and D** in the Operators tab (rows 6-15) were populated with training history data to support local DGET lookups

3. The spreadsheet was designed to compare multiple players' games - the Entry tab contains sections labeled "andy" and "Shorty" with their operator assignments

---

## Appendix B: Calibration Data

See [calibration_report.md](calibration_report.md) for detailed calibration findings from comparing the simulation against original REPT files.

Key findings:
- Production rates match documentation exactly
- Reject rate varies 1.5% - 17.8% (influenced by quality budget, floor at ~1.5%)
- Operator efficiency ranges: trained 95-120%, untrained 20-67%
- All verified cost constants match original files
- Fixed operator profiles: Operators 1-9 have consistent ceilings across game instances

---

*This documentation is part of the PROSIM Reconstruction Project. For player documentation, see [game_manual.md](game_manual.md).*
