# PROSIM Reconstruction - Implementation Plan

## Project Overview

**Goal**: Reconstruct PROSIM, a production management simulation game originally created in 1968, as a modern open-source application for educational preservation and practical use.

**Original Software**: PROSIM by Greenlaw, Hottenstein, and Chu (1968-1996)
- Original platform: IBM mainframes (FORTRAN) → Windows 3.1/95
- Status: Abandonware, no known copies exist online
- Documentation: Reconstructed from reverse-engineered spreadsheets and data files

**This Reconstruction**:
- Platform: Python (core) + Web UI (future)
- License: MIT
- Primary mode: Single-player self-service
- Architecture: Designed to support multiplayer (for preservation fidelity)

---

## Source Materials

The following files from the original coursework inform this reconstruction:

### Primary Evidence (High Value)
| File | Purpose | Location |
|------|---------|----------|
| `ProsimTable.xls` | Reverse-engineered simulation model (~97% accuracy) | `archive/` |
| `REPT*.DAT` files | Original simulation output (4 files across weeks 12-14) | `archive/data/` |
| `DECS*.DAT` files | Original decision input files | `archive/data/` |
| `week1.txt` | Human-readable report (Rosetta Stone for file format) | `archive/data/` |

### Supporting Materials
| File | Purpose | Location |
|------|---------|----------|
| `Prosim Template.xls` | Weekly planning template with field descriptions | `archive/` |
| `Prosim spreadsheet.xls` | Earlier calculation spreadsheet | `archive/` |
| `475ProSim.ppt` | Course introduction slides | `archive/docs/` |
| `ProSim_intro.ppt` | Detailed simulation mechanics | `archive/docs/` |
| `PROSIM_CASE_STUDY.md` | Forensic analysis document | `archive/docs/` |

---

## Verified Game Mechanics

### Production System

```
Raw Materials → Parts Department → Parts (X', Y', Z') → Assembly Department → Products (X, Y, Z)
```

**Production Rates** (verified from spreadsheet):
| Item | Standard Rate | Department |
|------|---------------|------------|
| X' | 60 parts/hour | Parts |
| Y' | 50 parts/hour | Parts |
| Z' | 40 parts/hour | Parts |
| X | 40 units/hour | Assembly |
| Y | 30 units/hour | Assembly |
| Z | 20 units/hour | Assembly |

**Reject Rate**: ~17.8% (verified across multiple REPT files)

**Bill of Materials**:
- 1 unit of X requires 1 part X'
- 1 unit of Y requires 1 part Y'
- 1 unit of Z requires 1 part Z'

### Decision Variables (DECS File)

```
Line 1: [Week] [Company#] [QualityBudget] [MaintBudget] [RMOrderReg] [RMOrderExp]
Line 2: [PartOrderX'] [PartOrderY'] [PartOrderZ']
Lines 3-11: [MachineID] [TrainFlag] [PartType] [ScheduledHours]
```

**Machine Assignments**:
- Machines 1-4: Parts Department
- Machines 5-9 (or 1-5 in Assembly): Assembly Department
- TrainFlag: 0 = send for training, 1 = already trained/working

### Cost Structure (verified from week1.txt)

**Per-Product Costs**:
1. Labor
2. Machine Set-Up
3. Machine Repair (random)
4. Raw Materials
5. Purchased Finished Parts
6. Equipment Usage
7. Parts Carrying Cost
8. Products Carrying Cost
9. Demand Penalty

**Overhead Costs**:
1. Quality Planning (decision input)
2. Plant Maintenance (decision input)
3. Training Cost
4. Hiring Cost ($2,700 per new hire)
5. Layoff and Firing Cost ($200/week not scheduled, $400 termination)
6. Raw Materials Carrying Cost
7. Ordering Cost
8. Fixed Expense ($1,500/week)

### Lead Times

| Order Type | Lead Time |
|------------|-----------|
| Regular Raw Materials | 3 weeks |
| Expedited Raw Materials | 1 week (+$1,200) |
| Purchased Parts | 1 week |

### Unknown/Estimated Parameters

These parameters could not be definitively determined and should be **configurable**:

| Parameter | Estimate | Basis |
|-----------|----------|-------|
| Machine repair probability | ~10-15% per machine per week | Observed $400 costs appearing randomly |
| Untrained operator efficiency | 60-90% (variable) | Observed productive hours ranging 32.1-43.1 for untrained |
| Trained operator efficiency | 95-100% | Observed ~100% productive hours for trained |
| Quality budget impact | Unknown | Possibly affects reject rate |
| Maintenance budget impact | Unknown | Possibly affects repair probability |
| Demand generation | Mean ± std dev (300/200/100) | From presentations |

---

## Project Structure

```
prosim-reconstruction/
├── archive/                    # Preserved original files
│   ├── data/                   # DECS, REPT, txt files
│   ├── spreadsheets/           # XLS files
│   └── docs/                   # PPT files, case study
│
├── prosim/                     # Python package
│   ├── __init__.py
│   ├── models/                 # Data models
│   │   ├── __init__.py
│   │   ├── company.py          # Company state
│   │   ├── inventory.py        # Inventory tracking
│   │   ├── operators.py        # Workforce management
│   │   ├── machines.py         # Machine definitions
│   │   └── orders.py           # Order tracking
│   │
│   ├── engine/                 # Simulation engine
│   │   ├── __init__.py
│   │   ├── simulation.py       # Main simulation loop
│   │   ├── production.py       # Production calculations
│   │   ├── costs.py            # Cost calculations
│   │   └── demand.py           # Demand generation
│   │
│   ├── io/                     # File I/O
│   │   ├── __init__.py
│   │   ├── decs_parser.py      # Parse DECS files
│   │   ├── rept_writer.py      # Generate REPT files
│   │   └── state_io.py         # Save/load game state
│   │
│   ├── config/                 # Configuration
│   │   ├── __init__.py
│   │   ├── defaults.py         # Default parameters
│   │   └── schema.py           # Config validation
│   │
│   └── i18n/                   # Internationalization
│       ├── __init__.py
│       └── locales/
│           ├── en.json
│           └── es.json
│
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── test_production.py
│   ├── test_costs.py
│   ├── test_inventory.py
│   └── validation/             # Validation against original files
│       ├── __init__.py
│       └── test_against_original.py
│
├── cli/                        # Command-line interface
│   ├── __init__.py
│   └── main.py
│
├── web/                        # Web UI (Phase 4)
│   └── (future)
│
├── docs/                       # Documentation
│   ├── game_manual.md          # Player documentation
│   ├── algorithms.md           # Technical documentation
│   └── api.md                  # API reference
│
├── IMPLEMENTATION_PLAN.md      # This file
├── CHANGELOG.md                # Version history
├── README.md                   # Project overview
├── LICENSE                     # MIT License
├── pyproject.toml              # Python project config
└── .gitignore
```

---

## Implementation Phases

### Phase 1: Foundation & Data Models
**Goal**: Establish project structure, data models, and file parsing

#### Tasks

- [ ] **1.1** Initialize git repository and project structure
  - Create directory structure
  - Set up `pyproject.toml` with dependencies
  - Create `.gitignore`
  - Add MIT LICENSE
  - Write initial README.md

- [ ] **1.2** Archive original files
  - Copy DECS/REPT files to `archive/data/`
  - Copy spreadsheets to `archive/spreadsheets/`
  - Copy documentation to `archive/docs/`
  - Include PROSIM_CASE_STUDY.md

- [ ] **1.3** Implement data models
  - `Company`: Company state container
  - `Inventory`: Raw materials, parts, products tracking
  - `Operator`: Worker with training status, efficiency
  - `Machine`: Machine with department, current assignment
  - `Order`: Pending orders with type, amount, due week
  - `Decisions`: Parsed DECS file representation
  - `Report`: REPT file data structure

- [ ] **1.4** Implement DECS file parser
  - Parse all fields from DECS format
  - Validate input ranges
  - Unit tests against original files

- [ ] **1.5** Implement REPT file parser (for validation)
  - Parse all fields from REPT format
  - Create comparison utilities
  - Unit tests against original files

- [ ] **1.6** Implement configuration system
  - Define configurable parameters
  - Load from JSON/YAML files
  - Provide sensible defaults
  - Document all parameters

**Deliverables**:
- Working file parsers
- Complete data model
- Test coverage for I/O

---

### Phase 2: Core Simulation Engine
**Goal**: Implement the simulation logic with ~97% accuracy

#### Tasks

- [ ] **2.1** Implement inventory management
  - Raw material tracking
  - Parts inventory (X', Y', Z')
  - Products inventory (X, Y, Z)
  - Order receiving logic
  - Consumption calculations

- [ ] **2.2** Implement operator system
  - Training status tracking
  - Efficiency calculations (trained vs untrained)
  - Consecutive scheduling tracking (layoff/termination)
  - Hiring logic

- [ ] **2.3** Implement production engine
  - Parts Department production
  - Assembly Department production
  - Setup time calculations
  - Reject calculations
  - Raw material consumption

- [ ] **2.4** Implement cost calculations
  - Per-product costs (all 9 categories)
  - Overhead costs (all 8 categories)
  - Weekly vs cumulative tracking

- [ ] **2.5** Implement demand system
  - Demand generation (configurable)
  - Shipping/fulfillment logic
  - Demand penalty calculations
  - Carryover tracking

- [ ] **2.6** Implement main simulation loop
  - Week-by-week processing
  - State transitions
  - Report generation

- [ ] **2.7** Implement REPT file writer
  - Match original format exactly
  - Support human-readable format (like week1.txt)

**Deliverables**:
- Complete simulation engine
- REPT output matching original format

---

### Phase 3: Validation & Calibration
**Goal**: Validate against original files and calibrate unknown parameters

#### Tasks

- [ ] **3.1** Create validation test suite
  - Load original DECS files
  - Run through simulation
  - Compare to original REPT files
  - Calculate accuracy metrics

- [ ] **3.2** Calibrate production parameters
  - Verify production rates
  - Calibrate reject rate
  - Adjust if needed

- [ ] **3.3** Calibrate operator efficiency
  - Model untrained efficiency curve
  - Verify trained efficiency
  - Document findings

- [ ] **3.4** Calibrate cost parameters
  - Derive labor rates
  - Derive equipment rates
  - Derive carrying cost rates
  - Document all derived values

- [ ] **3.5** Handle stochastic elements
  - Implement machine repair randomness
  - Implement demand variation
  - Make random seed configurable for reproducibility

- [ ] **3.6** Document accuracy
  - Calculate overall accuracy vs original
  - Document known discrepancies
  - Explain sources of variance

**Deliverables**:
- Validation test suite passing
- Documented accuracy metrics
- Calibrated default parameters

---

### Phase 4: CLI & Single-Player Mode
**Goal**: Create playable command-line interface

#### Tasks

- [ ] **4.1** Implement game state persistence
  - Save/load game state (JSON)
  - Support multiple save slots
  - Auto-save after each week

- [ ] **4.2** Implement CLI interface
  - New game setup
  - Display current state
  - Enter decisions interactively
  - Process week
  - Display reports
  - Save/load games

- [ ] **4.3** Implement decision validation
  - Validate machine assignments
  - Validate budget inputs
  - Validate order quantities
  - Helpful error messages

- [ ] **4.4** Implement reporting
  - Weekly report display
  - Cumulative summaries
  - Performance metrics
  - Export to various formats

- [ ] **4.5** Add i18n support
  - Extract all user-facing strings
  - Implement locale loading
  - Create English translations
  - Create Spanish translations (stretch)

**Deliverables**:
- Playable CLI game
- Save/load functionality
- Internationalization framework

---

### Phase 5: Web Interface (Future)
**Goal**: Create web-based UI for broader accessibility

#### Tasks

- [ ] **5.1** Design web architecture
  - Choose framework (FastAPI + React/Vue/HTMX)
  - Design API endpoints
  - Design database schema (if needed)

- [ ] **5.2** Implement backend API
  - REST/GraphQL endpoints
  - Authentication (simple)
  - Game state management

- [ ] **5.3** Implement frontend
  - Decision entry form
  - Report display
  - Game state visualization
  - Responsive design

- [ ] **5.4** Implement self-service "teacher"
  - Automatic week processing
  - AI competitor companies (optional)
  - Leaderboards (optional)

- [ ] **5.5** Deployment
  - Docker containerization
  - Deployment documentation
  - Hosting options

**Deliverables**:
- Web-playable version
- Deployment documentation

---

### Phase 6: Documentation & Preservation
**Goal**: Complete documentation for long-term preservation

#### Tasks

- [ ] **6.1** Write player documentation
  - Game rules and objectives
  - Decision guide
  - Strategy tips (from original course materials)

- [ ] **6.2** Write technical documentation
  - Algorithm documentation
  - API reference
  - Configuration guide

- [ ] **6.3** Historical documentation
  - Include case study
  - Document original authors
  - Link to LGIRA archive
  - Explain preservation motivation

- [ ] **6.4** Contribution guide
  - How to contribute translations
  - How to report issues
  - How to add features

- [ ] **6.5** Archive submission
  - Prepare for Internet Archive
  - Contact LGIRA about supplementary materials
  - Create release packages

**Deliverables**:
- Complete documentation
- Archive-ready package

---

## Development Guidelines

### Code Style
- Python 3.11+
- Type hints throughout
- Docstrings for all public functions
- Black for formatting
- Ruff for linting
- 80%+ test coverage target

### Git Workflow
- `main` branch for stable releases
- Feature branches for development
- Conventional commits (feat:, fix:, docs:, etc.)
- Tag releases with semantic versioning

### Testing Strategy
- Unit tests for all modules
- Integration tests for simulation accuracy
- Validation tests against original REPT files
- Property-based tests for edge cases (hypothesis)

### Dependencies (Initial)
```toml
[project]
dependencies = [
    "pydantic>=2.0",      # Data validation
    "click>=8.0",         # CLI framework
    "rich>=13.0",         # Terminal formatting
    "pytest>=7.0",        # Testing
    "pytest-cov>=4.0",    # Coverage
]

[project.optional-dependencies]
dev = [
    "black",
    "ruff",
    "mypy",
    "hypothesis",
]
web = [
    "fastapi",
    "uvicorn",
    "jinja2",
]
```

---

## Success Criteria

### Phase 1-3 (Core)
- [ ] Simulation produces output within 97% accuracy of original REPT files
- [ ] All original DECS files can be parsed
- [ ] All original REPT files can be parsed and compared
- [ ] Configuration allows tuning unknown parameters

### Phase 4 (CLI)
- [ ] Complete game can be played from command line
- [ ] Game state persists between sessions
- [ ] Reports match original format

### Phase 5 (Web)
- [ ] Game playable in web browser
- [ ] No installation required for players
- [ ] Mobile-responsive

### Phase 6 (Preservation)
- [ ] Documentation sufficient for future developers
- [ ] Historical context preserved
- [ ] Submitted to relevant archives

---

## Progress Log

### [Date] - Phase X.X - Task Description
_Status: Not Started | In Progress | Complete | Blocked_

Notes and findings will be logged here as work progresses.

---

## References

- [LGIRA Archive Entry](https://www.lgira.mesmernet.org/items/show/2717) - Original 1968 PROSIM catalog
- [Amazon - PROSIM 1969](https://www.amazon.com/PROSIM-Production-Management-Paul-Greenlaw/dp/0700222243) - Original textbook
- [Amazon - PROSIM III 1996](https://www.amazon.com/Prosim-Windows-Production-Management-Simulation/dp/0256214360) - Windows version
- [Penn State - Chao-Hsien Chu](https://www.psu.edu/news/information-sciences-and-technology/story/chao-hsien-chu-one-ists-original-five-faculty-members-has) - Co-author obituary
- `archive/docs/PROSIM_CASE_STUDY.md` - Detailed forensic analysis

---

*Plan created: December 2024*
*Last updated: December 2024*
