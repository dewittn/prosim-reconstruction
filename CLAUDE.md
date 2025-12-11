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
| `spreadsheets/Nelson.xls` | Reconstructed (Dec 2025) | External data file for ProsimTable.xls (see below) |
| `*.xtc` | Original game | Binary game state files |

**Important**: REPT12/13/14 are from DIFFERENT game runs (cumulative costs decrease), not sequential weeks.

### Nelson.xls - External Data Dependency

`ProsimTable.xls` contains formulas that reference an external file `Nelson.xls` for operator training history lookups. The original file was lost, but was reconstructed in December 2025 based on:

1. **Formula analysis** from ProsimTable.xls Operators tab (DGET/DSUM functions)
2. **Existing training data** visible in the spreadsheet
3. **Reverse-engineering** the required database structure

**Structure of Nelson.xls (Sheet1):**
- **Rows 2-30, Columns A-B**: Operator base lookup (`op`, `base`)
- **Rows 34-62, Columns A-E**: Training accumulator (`op`, `week`, `days_wo`, `days_with`, `op` for lookup)
- **Rows 34-62, Columns G-H**: Trained weeks accumulator (`op`, `trained`)

**To use ProsimTable.xls:**
The spreadsheet expects Nelson.xls at path `C:\Operators\Nelson.xls` (Windows). Update the external references in Excel via Data → Edit Links if using a different location.

**Related files created for other players' data:**
The Entry tab in ProsimTable.xls shows data labeled "andy" and "Shorty", suggesting similar external files (Andy.xls, Shorty.xls) may have existed for comparing different players' game runs.

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
| `docs/forensic_verification_status.md` | **START HERE** - Consolidated verification status of all mechanics |
| `docs/key_discoveries.md` | Chronicle of major forensic discoveries with evidence |
| `IMPLEMENTATION_PLAN.md` | Detailed roadmap and progress log |
| `docs/algorithms.md` | Technical documentation of all algorithms |
| `docs/verification_guide.md` | How to verify mechanics against original files |
| `docs/xtc_verification_guide.md` | XTC binary file analysis and open hypotheses |
| `prosim/config/defaults.py` | All game constants with verification notes |
| `prosim/io/rept_parser.py` | REPT file parsing and human-readable output |
| `archive/docs/PROSIM_CASE_STUDY.md` | Original forensic analysis and history |

## Verification Status Summary

Before modifying simulation mechanics, check `docs/forensic_verification_status.md` for confidence levels:

| Status | Meaning | Action |
|--------|---------|--------|
| ✅ VERIFIED | Confirmed against original data | Do not change without explicit request |
| ⚠️ PARTIAL | Partially understood | Changes OK, document reasoning |
| ❓ UNKNOWN | Estimated/hypothesized | Make configurable, flag uncertainty |

**Key verified items**: Production rates, training matrix, cost constants, lead times
**Key unknowns**: Machine repair probability, XTC Float2 meaning, maintenance budget effect

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
5. **Record Key Discoveries**: When you discover something significant about the original simulation (unexpected data patterns, formula corrections, hidden data, etc.), **add it to `docs/key_discoveries.md`** using the template provided there
