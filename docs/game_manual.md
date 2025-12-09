# PROSIM Game Manual

> A Production Management Simulation for Learning Operations Management

## Table of Contents

1. [Introduction](#introduction)
2. [Quick Start Guide](#quick-start-guide)
3. [Game Objective](#game-objective)
4. [Production System](#production-system)
5. [Weekly Decisions](#weekly-decisions)
6. [Understanding Reports](#understanding-reports)
7. [Strategy Guide](#strategy-guide)
8. [CLI Reference](#cli-reference)
9. [Glossary](#glossary)

---

## Introduction

PROSIM is a production management simulation game where you manage a manufacturing company that produces three products: X, Y, and Z. Originally developed in 1968 by Greenlaw, Hottenstein, and Chu at Penn State University, this reconstruction preserves the educational value of the classic simulation for modern use.

As a production manager, you will make weekly decisions about:
- **Production scheduling** - Which products to make and how many hours to allocate
- **Inventory management** - Ordering raw materials and parts
- **Workforce planning** - Training, hiring, and scheduling workers
- **Budget allocation** - Quality control and maintenance spending

The simulation runs for 15 weeks (configurable), with products shipping to customers every 4 weeks. Your goal is to meet customer demand while minimizing total costs.

### What You'll Learn

PROSIM teaches fundamental operations management concepts:
- Material Requirements Planning (MRP)
- Capacity planning and scheduling
- Inventory management and EOQ principles
- Workforce management and training economics
- Cost-benefit analysis of expediting options
- Demand forecasting under uncertainty

---

## Quick Start Guide

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/prosim-reconstruction.git
cd prosim-reconstruction

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install the package
pip install -e .
```

### Starting Your First Game

```bash
# Start a new game
prosim new --name "My Company"

# Or with a specific random seed (for reproducibility)
prosim new --name "My Company" --seed 42
```

### Your First Week

When the game starts, you'll see your company's current state and be prompted for decisions. For your first week, try these starting values:

| Decision | Recommended Value | Why |
|----------|-------------------|-----|
| Quality Budget | $500-750 | Reduces reject rate |
| Maintenance Budget | $500 | Reduces machine breakdowns |
| Raw Materials (Regular) | 10,000-15,000 | 3-week lead time, plan ahead |
| Raw Materials (Expedited) | 0 | Avoid $1,200 surcharge initially |
| Parts Orders (X'/Y'/Z') | 500/400/300 | Buffer stock for assembly |
| Machine Hours | 40 hours each | Standard work week |

### Basic Workflow

1. **Review** your current inventory and pending orders
2. **Forecast** demand for the shipping period
3. **Plan** production to meet forecasted demand
4. **Order** materials with appropriate lead times
5. **Schedule** machines and operators
6. **Process** the week and review results
7. **Adjust** strategy based on outcomes

---

## Game Objective

### Primary Goal

**Minimize total costs while meeting customer demand.**

Your performance is measured by:
- **Total costs** - Lower is better
- **On-time delivery %** - Higher is better
- **Efficiency %** - Actual vs. standard performance

### The Challenge

Managing a manufacturing operation requires balancing multiple competing concerns:

- **Too much inventory** = High carrying costs
- **Too little inventory** = Stockouts and demand penalties
- **Too many workers** = Labor costs when idle
- **Too few workers** = Overtime or missed production
- **Rush orders** = Expensive expediting fees
- **No rush orders** = Potential stockouts

### Winning Strategy

The best managers:
1. Plan 3-4 weeks ahead (matching raw material lead times)
2. Build appropriate safety stock before shipping periods
3. Train operators early for improved efficiency
4. Use expediting sparingly and strategically
5. Balance quality spending against reject rates

---

## Production System

### Production Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PRODUCTION FLOW                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Raw Materials                                                       │
│       │                                                              │
│       ▼                                                              │
│  ┌─────────────────────────────────────┐                            │
│  │       PARTS DEPARTMENT              │                            │
│  │       Machines 1-4                  │                            │
│  │                                     │                            │
│  │   Raw Materials ──► Parts           │                            │
│  │   • X' parts: 60/hour               │                            │
│  │   • Y' parts: 50/hour               │                            │
│  │   • Z' parts: 40/hour               │                            │
│  └─────────────────────────────────────┘                            │
│       │                                                              │
│       ▼                                                              │
│  ┌─────────────────────────────────────┐                            │
│  │      ASSEMBLY DEPARTMENT            │                            │
│  │      Machines 5-9                   │                            │
│  │                                     │                            │
│  │   Parts ──► Finished Products       │                            │
│  │   • X products: 40/hour             │                            │
│  │   • Y products: 30/hour             │                            │
│  │   • Z products: 20/hour             │                            │
│  └─────────────────────────────────────┘                            │
│       │                                                              │
│       ▼                                                              │
│  Finished Goods Inventory ──► Customer Shipments (every 4 weeks)    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Bill of Materials

Each finished product requires exactly one part of the corresponding type:
- 1 unit of Product X requires 1 X' part
- 1 unit of Product Y requires 1 Y' part
- 1 unit of Product Z requires 1 Z' part

Each part requires raw materials to produce (the simulation handles this automatically).

### Production Rates

| Department | Product/Part | Standard Rate |
|------------|--------------|---------------|
| Parts | X' | 60 parts/hour |
| Parts | Y' | 50 parts/hour |
| Parts | Z' | 40 parts/hour |
| Assembly | X | 40 products/hour |
| Assembly | Y | 30 products/hour |
| Assembly | Z | 20 products/hour |

### Production Formula

```
Productive Hours = (Scheduled Hours - Setup Time) × Operator Efficiency
Gross Production = Productive Hours × Production Rate
Rejects = Gross Production × Reject Rate
Net Production = Gross Production - Rejects
```

### Setup Time

When a machine switches to producing a different part/product type:
- **Setup time**: 2-4 hours (subtracted from scheduled hours)
- **Avoid switching** part types when possible to maximize productive time

### Reject Rate

- **Base reject rate**: ~12-18% of production
- **Quality budget** reduces the reject rate
- Higher quality spending = fewer rejects = more good units

---

## Weekly Decisions

Each week you submit decisions in five categories:

### 1. Budget Allocations

| Budget | Recommended | Effect |
|--------|-------------|--------|
| **Quality Planning** | $500-750 | Reduces reject rate |
| **Plant Maintenance** | $500 | Reduces machine breakdown probability |

**Tips:**
- Quality budget has diminishing returns above $750
- Maintenance budget reduces random $400 repair costs

### 2. Raw Materials Orders

| Order Type | Lead Time | Extra Cost |
|------------|-----------|------------|
| **Regular** | 3 weeks | None |
| **Expedited** | 1 week | +$1,200 |

**Tips:**
- Plan regular orders 3+ weeks ahead
- Use expedited only in emergencies
- Order enough for Parts Department production needs

### 3. Purchased Parts Orders

| Order Type | Lead Time | Cost |
|------------|-----------|------|
| **X' Parts** | 1 week | Market price |
| **Y' Parts** | 1 week | Market price |
| **Z' Parts** | 1 week | Market price |

**Tips:**
- Alternative to in-house parts production
- Useful when Parts Department capacity is constrained
- Consider vs. cost of in-house production

### 4. Machine Assignments

For each of the 9 machines, you specify:
- **Part type** (1=X/X', 2=Y/Y', 3=Z/Z')
- **Scheduled hours** (0-50 hours per week)
- **Training** (send operator for training instead of working)

**Department assignments:**
- Machines 1-4: Parts Department (produce X', Y', Z')
- Machines 5-9: Assembly Department (produce X, Y, Z)

### 5. Operator Training

- Operators can be sent for **1 week of training**
- During training, operator produces nothing
- After training, efficiency improves to 95-100%
- Untrained operators have 60-90% efficiency

---

## Understanding Reports

After each week, you receive a detailed report with several sections:

### Cost Report

**Per-Product Costs (X, Y, Z):**
| Cost Category | Description |
|---------------|-------------|
| Labor | $10/hour for productive time |
| Machine Set-Up | Setup time when switching products |
| Machine Repair | Random breakdowns ($400 each) |
| Raw Materials | Materials consumed in production |
| Purchased Parts | Cost of ordered finished parts |
| Equipment Usage | $20/hour for machine operation |
| Parts Carrying | Cost of holding parts inventory |
| Products Carrying | Cost of holding product inventory |
| Demand Penalty | Penalty for unfulfilled demand |

**Overhead Costs:**
| Cost Category | Description |
|---------------|-------------|
| Quality Planning | Your quality budget decision |
| Plant Maintenance | Your maintenance budget decision |
| Training Cost | $1,000 per operator in training |
| Hiring Cost | $2,700 per new hire |
| Layoff Cost | $200/week for unscheduled operators |
| Termination Cost | $400 after 2+ weeks unscheduled |
| RM Carrying Cost | Cost of holding raw materials |
| Ordering Cost | Cost per order placed |
| Fixed Expense | $1,500/week (constant) |

### Production Report

Shows for each machine:
- Operator assigned
- Part/product type being made
- Scheduled hours
- Productive hours (after efficiency)
- Units produced
- Rejects

### Inventory Report

Shows for each inventory type:
- Beginning inventory
- Orders received (parts, raw materials)
- Production this week
- Used in production / shipped to customers
- Ending inventory

### Demand Report

Shows:
- Estimated demand for current shipping period
- Carryover from previous periods (unfulfilled demand)
- Total demand to meet

### Performance Measures

| Measure | Description |
|---------|-------------|
| Standard Cost | Expected cost at 100% efficiency |
| Actual Cost | Your actual costs |
| Efficiency % | Actual/Standard × 100 |
| Variance/Unit | Cost over/under standard |
| On-Time % | Orders fulfilled on time |

---

## Strategy Guide

### Week 1-4: Startup Phase

**Goals:**
- Build initial inventory buffer
- Get operators trained
- Establish steady production rhythm

**Recommended Actions:**
1. Order raw materials (regular) - plan for week 4-5 production
2. Order purchased parts as buffer stock
3. Train 2-3 operators in first two weeks
4. Don't worry about perfect efficiency yet

**Sample Week 1 Decisions:**
```
Quality Budget: $750
Maintenance Budget: $500
Raw Materials (Regular): 12,000
Raw Materials (Expedited): 0
Parts X'/Y'/Z': 500/400/300
All machines: 40 hours, current product
Consider: 1-2 operators for training
```

### Week 5-8: Production Phase

**Goals:**
- Meet first shipping demand (week 4)
- Build inventory for week 8 shipping
- Optimize production mix

**Recommended Actions:**
1. Review demand forecast for week 8
2. Calculate parts needed for assembly
3. Calculate raw materials needed for parts
4. Adjust production hours to match demand mix

### Week 9-12: Optimization Phase

**Goals:**
- Fine-tune inventory levels
- Minimize carrying costs
- Maintain on-time delivery

**Recommended Actions:**
1. Reduce orders if inventory is high
2. Reduce quality/maintenance if no problems
3. Focus production on high-demand products

### Week 13-15: Endgame

**Goals:**
- Meet final demand
- Don't leave excess inventory (carrying cost)
- Maximize efficiency rating

**Recommended Actions:**
1. Calculate exact needs for final shipping
2. Stop ordering raw materials (won't arrive in time)
3. Use up inventory, don't build more

### Common Mistakes to Avoid

1. **Not ordering raw materials early enough**
   - 3-week lead time means order in week 1 for week 4 use

2. **Forgetting setup time**
   - Switching products costs 2-4 hours per machine
   - Keep machines on same product when possible

3. **Training operators during peak production**
   - Train during slow periods or early in game

4. **Over-expediting**
   - $1,200 per expedited order adds up quickly

5. **Ignoring the reject rate**
   - Quality budget pays for itself in reduced waste

6. **Not planning for demand variability**
   - Keep safety stock for uncertain demand

### Demand Forecasting

Demand forecasts become more accurate as shipping approaches:

| Weeks Until Shipping | Uncertainty (σ) |
|---------------------|-----------------|
| 4 weeks | ±300 units |
| 3 weeks | ±300 units |
| 2 weeks | ±200 units |
| 1 week | ±100 units |
| Shipping week | Exact (σ=0) |

**Strategy:** Plan for average demand early, then adjust as forecast firms up.

---

## CLI Reference

### Commands

```bash
# Start new game
prosim new --name "Company Name" [--weeks 15] [--seed 42]

# Load saved game
prosim load <slot>           # Load from save slot
prosim load --autosave       # Load from autosave

# List saved games
prosim saves

# Process week with DECS file
prosim process --decs input.DAT [--slot 1] [--output report.txt]

# Show information
prosim info

# Show help
prosim --help
```

### Interactive Mode Options

When playing interactively, you have these choices:
1. **Enter decisions** - Submit weekly decisions
2. **View last report** - Review previous week's results
3. **Save game** - Save to a slot
4. **Help** - Show in-game help
5. **Quit** - Exit (with save option)

### Save System

- **Autosave**: Automatic save after each week
- **Manual saves**: Slots 1-99 available
- **Save location**: `~/.local/share/prosim/saves/`

### Language Support

```bash
# Play in Spanish
prosim --lang es new --name "Mi Empresa"
```

---

## Glossary

| Term | Definition |
|------|------------|
| **Assembly Department** | Machines 5-9; converts parts into finished products |
| **Carrying Cost** | Cost of holding inventory over time |
| **DECS File** | Decision input file format |
| **Demand Penalty** | Cost for unfulfilled customer orders |
| **Expedited Order** | Rush order with 1-week lead time and extra cost |
| **Lead Time** | Time between ordering and receiving materials |
| **Parts Department** | Machines 1-4; converts raw materials into parts |
| **Productive Hours** | Actual working hours after efficiency applied |
| **Reject Rate** | Percentage of production that fails quality |
| **REPT File** | Report output file format |
| **Scheduled Hours** | Hours assigned to a machine for the week |
| **Setup Time** | Time lost when switching product types |
| **Shipping Period** | Every 4 weeks, products ship to customers |

---

## Appendix: Default Configuration

### Starting Inventory

| Item | Starting Amount |
|------|-----------------|
| Raw Materials | 20,000 units |
| X' Parts | 2,000 units |
| Y' Parts | 1,500 units |
| Z' Parts | 1,000 units |
| X Products | 1,000 units |
| Y Products | 750 units |
| Z Products | 500 units |

### Default Demand

| Product | Average Demand per Period |
|---------|---------------------------|
| X | 600 units |
| Y | 400 units |
| Z | 200 units |

### Cost Parameters

| Parameter | Value |
|-----------|-------|
| Labor (hourly) | $10.00 |
| Equipment (hourly) | $20.00 |
| Machine Repair | $400.00/incident |
| Hiring Cost | $2,700.00/new hire |
| Layoff Cost | $200.00/week |
| Termination | $400.00 (after 2 weeks) |
| Fixed Expense | $1,500.00/week |
| Training Cost | $1,000.00/session |
| Expedite Fee | $1,200.00/order |

---

*This documentation is part of the PROSIM Reconstruction Project. For technical details, see [calibration_report.md](calibration_report.md). For historical context, see [PROSIM_CASE_STUDY.md](../archive/docs/PROSIM_CASE_STUDY.md).*
