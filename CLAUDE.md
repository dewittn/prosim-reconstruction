# CLAUDE.md - PROSIM Reconstruction Project

## Project Overview

This is a reconstruction of **PROSIM III**, a production management simulation game originally created in 1968 by Greenlaw, Hottenstein, and Chu. The original Windows software from 1996 is lost/unavailable, so we're rebuilding it from forensic analysis of archived game files from a 2004 college course.

**Goal**: Create a faithful recreation that produces identical results to the original simulation when given the same inputs.

## Background Story

- **2003-2004**: The project owner played PROSIM as a student in MGMT475 and reverse-engineered the game mechanics using spreadsheet analysis
- **Senior Year Project**: Attempted to reconstruct PROSIM; instructor provided access to teacher-side files
- **December 2025**: Resuming the reconstruction with Claude's assistance, using the preserved archive files

## Archive Structure

The `/archive` folder contains original files from 2004:

| Folder/File | Source | Description |
|-------------|--------|-------------|
| `data/DECS*.DAT` | Student (owner) | Decision input files (Company 1) |
| `data/REPT12.DAT` | Instructor | Andy's Week 12 report (Company 2) |
| `data/REPT13.DAT` | Instructor | Shorty's Week 13 report (Company 2) |
| `data/REPT14.DAT` | Instructor | Unknown student's Week 14 (Company 2) |
| `data/week1.txt` | Original game | Human-readable Week 1 report (Rosetta Stone!) |
| `spreadsheets/ProsimTable.xls` | Student (owner) | Reverse-engineered simulation spreadsheet |
| `*.xtc` | Original game | Binary game state files |

**Important**: REPT12/13/14 are from DIFFERENT game runs (cumulative costs decrease), not sequential weeks.

## Key Discoveries (December 2025)

### 1. Reject Rate Formula (Logarithmic)
```python
reject_rate = 0.904 - 0.114 * ln(quality_budget)
# Floor at ~1.5%
```
Verified against Graph-Table 1 from original spreadsheet analysis.

### 2. Training Matrix (11 levels x 10 tiers)
Exact efficiency values extracted from `ProsimTable.xls` and verified against XTC game state files with 0.2% average error. See `prosim/config/defaults.py`.

### 3. Two-Component Efficiency Model
```
Output = Scheduled_Hours × Time_Efficiency × Rate × Proficiency
```
- **Time Efficiency**: Improves with training (from training matrix)
- **Proficiency**: Fixed at hire (quality tier ceiling)

### 4. Operator Ceiling Concept
Starting operators (1-9) have FIXED profiles across all game instances:
- Operator 3: Always expert (~132% ceiling)
- Operators 4,5,6,8,9: Low tier (50-60% ceiling)
- Hired operators (10+): Randomized tiers

### 5. Game Efficiency Formula
```
Game Efficiency = (Standard Costs / Actual Costs) × 100%
```
The "shutdown strategy" exploits this: build inventory, cut production, ship from stock.

### 6. Report Format Verification
REPT files (machine-readable) and week1.txt (human-readable) contain identical data. The `write_rept_human_readable()` function now generates authentic 2004 format.

## Key Files

| File | Purpose |
|------|---------|
| `IMPLEMENTATION_PLAN.md` | Detailed roadmap and progress log |
| `docs/algorithms.md` | Technical documentation of all algorithms |
| `docs/verification_guide.md` | How to verify mechanics against original files |
| `prosim/config/defaults.py` | All game constants with verification notes |
| `prosim/io/rept_parser.py` | REPT file parsing and human-readable output |

## Current Implementation Status

- **Phase 1-4**: Complete (Core models, engine, CLI)
- **Phase 5**: In progress (Web interface)
- **Phase 6**: Mostly complete (Documentation)

The simulation engine is functional. Key areas still being refined:
- Operator efficiency model (simplified vs. full two-component)
- Stochastic elements calibration

## Commands

```bash
# Run CLI
cd prosim-reconstruction
.venv/bin/python -m prosim.cli.main

# Run tests
.venv/bin/pytest

# Run web interface
.venv/bin/uvicorn web.app:app --reload
```

## Original Data Location

The original archive files are in a sibling directory:
```
/Users/dewittn/Programing/dewittn/Other/Prosim/
```

This contains the raw 2004 files including:
- `ProsimTable CVS Export/` - Spreadsheet analysis tabs
- `A/` - Additional DECS/REPT files
- `475ProSim.ppt` - Instructor's course presentation
- `report.doc` - Human-readable report (Word format)

## Key Principles

1. **Historical Accuracy**: Match original behavior exactly where possible
2. **Document Everything**: All discoveries go in IMPLEMENTATION_PLAN.md
3. **Verify Against Archive**: Use original files to validate formulas
4. **Authentic Output**: Reports should match what students saw in 2004
