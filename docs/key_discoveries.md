# PROSIM Reconstruction - Key Discoveries

> **Purpose**: This document chronicles the major discoveries made during the forensic reconstruction of PROSIM. Each discovery is documented with evidence, implications, and references.
>
> **For Claude Code Agents**: Review this document to understand critical context about the original data. Many discoveries reveal that our source data is more complex than it first appears.

---

## Adding New Discoveries

**IMPORTANT**: When you discover something significant about the original PROSIM simulation, **add it to this document**. A discovery is worth documenting if it:

1. **Reveals unexpected data characteristics** (e.g., files from different sources than assumed)
2. **Corrects a previous assumption** (e.g., formula is logarithmic not linear)
3. **Unlocks new understanding** (e.g., hidden data in binary files)
4. **Has strategic implications** (e.g., operator profiles are fixed)
5. **Recovers lost information** (e.g., reconstructing missing files)

### Template for New Discoveries

```markdown
## [N]. [Discovery Title]

**Date Discovered**: [Month Year]

**Category**: [Data Integrity | Core Mechanic | Formula Correction | etc.]

### The Discovery

[1-2 sentence summary of what was discovered]

### Evidence

[Concrete data, file references, calculations that prove the discovery]

### Implications

1. [Why this matters for the reconstruction]
2. [How it affects validation/implementation]
3. [Strategic insights if any]

### References
- [File paths and line numbers]
- [Related documentation]
```

### After Adding a Discovery

1. Update the **Discovery Index** table at the top
2. Increment the discovery number
3. Update the **Document History** at the bottom
4. Consider if `forensic_verification_status.md` needs updating

---

## Discovery Index

| # | Discovery | Date | Impact |
|---|-----------|------|--------|
| 1 | [REPT Files Are From Different Games](#1-rept-files-are-from-different-games) | Dec 2025 | Critical - Affects validation |
| 2 | [ProsimTable.xls Links to External Nelson.xls](#2-prosimtablexls-links-to-external-nelsonxls) | Dec 2025 | Important - Spreadsheet dependency |
| 3 | [Reject Rate is Logarithmic](#3-reject-rate-is-logarithmic-not-linear) | Dec 2025 | Important - Formula correction |
| 4 | [Two-Component Efficiency Model](#4-two-component-efficiency-model) | Dec 2025 | Critical - Core mechanic |
| 5 | [Operator 3 is Always Expert](#5-operator-3-is-always-expert) | Dec 2025 | Important - Fixed profiles |
| 6 | [XTC Files Contain Hidden Operator Stats](#6-xtc-files-contain-hidden-operator-stats) | Dec 2025 | Critical - New data source |
| 7 | [Training Matrix Verified to 0.2% Error](#7-training-matrix-verified-to-02-error) | Dec 2025 | High confidence |
| 8 | [week1.txt is Rosetta Stone for REPT Format](#8-week1txt-is-rosetta-stone-for-rept-format) | Dec 2025 | Important - Format understanding |
| 9 | [Game Efficiency vs Operator Efficiency](#9-game-efficiency-vs-operator-efficiency) | Dec 2025 | Important - Terminology |
| 10 | [Nelson.xls Structure Reconstructed](#10-nelsonxls-structure-reconstructed) | Dec 2025 | Data recovery |
| 11 | [ProsimTable.xls Evolution Traced](#11-prosimtablexls-evolution-traced) | Dec 2025 | Archive insight |

---

## 1. REPT Files Are From Different Games

**Date Discovered**: December 2025

**Category**: Data Integrity

### The Discovery

REPT12.DAT, REPT13.DAT, and REPT14.DAT are **NOT sequential weeks from the same game**. They are from **different game runs** by different players.

### Evidence

**Cumulative costs DECREASE between files** (impossible if sequential):

| File | Cumulative Total Cost | Player Label |
|------|----------------------|--------------|
| REPT12.DAT | Higher | "Andy" |
| REPT13.DAT | Middle | "Shorty" |
| REPT14.DAT | Lower | "Nelson" |

In a sequential game, cumulative costs can only increase. The decrease proves these are independent games.

**Additional evidence**:
- Different operator assignments visible in production sections
- Different inventory levels that don't flow logically
- The spreadsheet Entry tab shows columns labeled "andy" and "Shorty"

**XLS↔DAT file linkage verified (December 2025)**:
| XLS File | DAT File | First Row Match |
|----------|----------|-----------------|
| `AndyREPT.xls` | `REPT12.DAT` | `12.0, 2.0, 4.0, 4.0, 5.0` = Week 12, Company 2 |
| `ShortyREPT.xls` | `REPT13.DAT` | `13.0, 2.0, 4.0, 4.0, 5.0` = Week 13, Company 2 |
| `REPT.xls` | `REPT14.DAT` | `14.0, 2.0, 4.0, 4.0, 5.0` = Week 14, Company 2 |

**report.doc ownership confirmed**:
- File metadata: Author = "Nelson de Wilt", Created May 20, 2004
- Content matches REPT14.DAT exactly (field-by-field)
- Proves REPT14.DAT belongs to Nelson

**week1.txt ownership UNKNOWN**:
- Week 1 data (weekly costs = cumulative costs, proving no prior weeks)
- No author metadata in text format
- Likely instructor-provided sample or from different game context

### Implications

1. **Cannot do end-to-end validation**: We can't feed DECS14 into our simulation and compare to REPT14 because we don't know the state before DECS14 was processed
2. **Cross-game comparisons ARE valid**: Comparing Operator 3's proficiency across files reveals fixed profiles
3. **Need matched pairs**: True validation requires DECS + REPT from the SAME game run

### References
- `CLAUDE.md` line 30
- `docs/forensic_verification_status.md` "Path to End-to-End Validation" section
- `docs/calibration_report.md` "Known Discrepancies" section

---

## 2. ProsimTable.xls Links to External Nelson.xls

**Date Discovered**: December 2025

**Category**: Data Dependency

### The Discovery

The main reverse-engineering spreadsheet `ProsimTable.xls` contains formulas that reference an external file `Nelson.xls` for operator training history lookups. This file was **lost** but has been **reconstructed**.

### Evidence

**Formula patterns found in Operators tab**:
```excel
=DGET('C:\Operators\[Nelson.xls]Sheet1'!$A$6:$E$34,$C$6,$J21:$J22)
=DSUM('C:\Operators\[Nelson.xls]Sheet1'!$G$34:$H$62,$H$34,$I21:$I22)
```

**DGET/DSUM functions** require a database structure with:
- Headers in row 6
- Data in subsequent rows
- Lookup criteria matching column structure

### Reconstruction

Nelson.xls was reconstructed based on:

1. **Formula analysis** - Identified required columns: `op`, `base`, `days_wo`, `days_with`
2. **Existing values** - Some values were visible in the Operators tab
3. **Reverse-engineering** - Derived the database structure needed for DGET to return observed values

**Reconstructed Structure**:
```
Sheet1:
  Rows 2-30, Cols A-B: Operator base lookup (op, base)
  Rows 34-62, Cols A-E: Training accumulator (op, week, days_wo, days_with, op)
  Rows 34-62, Cols G-H: Trained weeks accumulator (op, trained)
```

### Implications

1. **Spreadsheet won't work without Nelson.xls**: Opening ProsimTable.xls shows #REF! errors without it
2. **Path dependency**: Original expected `C:\Operators\Nelson.xls` (Windows path)
3. **Other players' files existed**: Entry tab references suggest Andy.xls, Shorty.xls also existed

### References
- `CLAUDE.md` "Nelson.xls - External Data Dependency" section
- `docs/algorithms.md` "Appendix A: ProsimTable.xls Spreadsheet Structure"
- `archive/spreadsheets/Nelson.xls` (reconstructed file)

---

## 3. Reject Rate is Logarithmic, Not Linear

**Date Discovered**: December 2025

**Category**: Formula Correction

### The Discovery

The reject rate follows a **logarithmic relationship** with quality budget, not linear. This creates diminishing returns - each additional dollar of quality budget reduces rejects less than the previous.

### Evidence

**Empirical data from Graph-Table 1.csv** (2004 spreadsheet):

| Quality Budget | Observed Reject Rate |
|----------------|---------------------|
| $750 | 15.14% |
| $850 | 13.02% |
| $1,000 | 10.00% |
| $1,200 | 7.94% |
| $2,000 | 4.00% |
| $2,500 | ~1.6% (floor) |

**Linear model would predict**:
- $750 → 15%
- $2,000 → negative (impossible!)

**Logarithmic fit**:
```python
reject_rate = 0.904 - 0.114 * ln(quality_budget)
# Floor at ~1.5%
```

### Implications

1. **Diminishing returns**: First $250 (750→1000) saves ~5% rejects; next $1000 (1000→2000) saves only ~6%
2. **Strategy insight**: Spending above ~$1,500 has minimal benefit
3. **Floor exists**: Can't reduce below ~1.5% regardless of budget

### References
- `prosim/config/defaults.py:calculate_reject_rate()`
- `docs/verification_guide.md` Section 6
- `archive/spreadsheets/ProsimTable CVS Export/Graph-Table 1.csv`

---

## 4. Two-Component Efficiency Model

**Date Discovered**: December 2025

**Category**: Core Mechanic

### The Discovery

Operator output is determined by **TWO separate hidden stats**, not one combined efficiency value:

```
Output = Scheduled_Hours × Time_Efficiency × Rate × Proficiency
```

| Component | Source | Behavior |
|-----------|--------|----------|
| **Time Efficiency** | Training level | Improves with training (64-103%) |
| **Proficiency** | Quality tier | Fixed at hire, never changes (51-122%) |

### Evidence

**From week1.txt operator data**:

| Operator | Sched Hrs | Prod Hrs | Output | Time Eff | Proficiency |
|----------|-----------|----------|--------|----------|-------------|
| Op 1 | 40 | 37.0 | 1556 | 92.5% | 70.1% |
| Op 3 | 40 | 37.0 | 1535 | 92.5% | **103.7%** |
| Op 5 | 40 | 40.0 | 1105 | 100.0% | 55.2% |

- **Time Efficiency** = Productive Hours ÷ Scheduled Hours
- **Proficiency** = Output ÷ (Productive Hours × Standard Rate)

**XTC file confirmation**: Two floats stored per operator (Float1 correlates with proficiency)

### Implications

1. **Training has limits**: Can't exceed proficiency ceiling through training
2. **Expert operators exist**: Proficiency >100% means exceeding "standard" rate
3. **Strategic hiring**: Low-proficiency operators (50-60%) will always underperform
4. **XTC stores both**: Binary files track both components separately

### References
- `docs/algorithms.md` Section 3 "Operator Efficiency Algorithm"
- `IMPLEMENTATION_PLAN.md` "Two-Component Efficiency Model" section
- `archive/data/week1.txt`

---

## 5. Operator 3 is Always Expert

**Date Discovered**: December 2025

**Category**: Fixed Profiles

### The Discovery

Starting operators (1-9) have **fixed profiles** that are consistent across ALL game instances. Operator 3 is ALWAYS an expert with >100% proficiency.

### Evidence

**Operator 3 proficiency across different games**:

| Game/Player | Week | Proficiency | Status |
|-------------|------|-------------|--------|
| Andy | 12 | 111.9% | Expert |
| Shorty | 13 | 108.9% | Expert |
| Nelson | 14 | 106.2% | Expert |
| week1.txt | 1 | 103.7% | Expert |

**Standard deviation**: 3.1% (remarkably consistent)

**Other operators show similar consistency**:
- Op 4, 5, 8, 9: Always low tier (50-60% ceiling)
- Op 7: Always strong (~110% ceiling)

### Implications

1. **Not random**: Starting operators have deterministic, reproducible profiles
2. **Strategy**: Always assign Operator 3 to highest-volume products
3. **Hired operators (10+) differ**: Appear to have randomized profiles
4. **Game balance**: Every player starts with same operator quality distribution

### References
- `prosim/config/defaults.py:STARTING_OPERATOR_PROFILES`
- `docs/forensic_verification_status.md` Section 5
- `IMPLEMENTATION_PLAN.md` "Operator Ceiling Concept" section

---

## 6. XTC Files Contain Hidden Operator Stats

**Date Discovered**: December 2025

**Category**: New Data Source

### The Discovery

The `.xtc` files (prosim.xtc, prosim1.xtc) are **PROSIM game state save files** containing hidden operator statistics not visible in REPT files. These files were obtained from Professor Rourke's computer during the **Summer 2005 senior project** (a first reconstruction attempt) but **never decoded until December 2025** - they sat as mystery binary files for over 20 years.

### Evidence

**File structure decoded**:
```
Header (87 bytes):
  Byte 9:  Number of operators
  Byte 40: Max simulation weeks (24)
  Byte 44: Week counter

Records delimited by 0x15 (ASCII NAK):
  [Float1:4 bytes][Float2:4 bytes][?:4 bytes][?:4 bytes]
```

**Float1 values correlate with proficiency** (scale factor 1.088):
```
XTC Float1 × 1.088 ≈ Derived Proficiency

1.0312 × 1.088 = 1.122 → Op 3 (Expert)  ✓ EXACT MATCH
0.9667 × 1.088 = 1.052 → Op 1           ✓
0.6397 × 1.088 = 0.696 → Op 6           ✓
```

**File size indicates game progress**:
- prosim.xtc (18,963 bytes) = Week 9, 9 operators
- prosim1.xtc (29,088 bytes) = Week 13, 13 operators (4 hired)

### Implications

1. **New validation source**: Can verify proficiency model against binary data
2. **Weekly snapshots**: File grows as game progresses (state history)
3. **Float2 unknown**: Second float's purpose still undetermined
4. **Instructor data**: These are from Professor Rourke's computer (instructor-side files)
5. **Not used in 2004**: All original reverse-engineering was done without this data - the training matrix and efficiency formulas were derived purely from REPT/DECS observation
6. **Obtained in 2005**: Files grabbed during senior project reconstruction attempt, sat undecoded for 20 years

### References
- `docs/xtc_verification_guide.md` (complete analysis)
- `archive/docs/PROSIM_CASE_STUDY.md` Appendix F
- `archive/data/prosim.xtc`, `archive/data/prosim1.xtc`

---

## 7. Training Matrix Verified to 0.2% Error

**Date Discovered**: December 2025

**Category**: High-Confidence Verification

### The Discovery

The 11-level × 10-tier training matrix extracted from ProsimTable.xls was verified against XTC file data with only **0.2% average error**.

### Evidence

**Matrix structure** (efficiency percentages):
```
         Level 0   A     B     C     D     E     F     G     H     I     J
Tier 0:    20%   61%   79%   89%   96%  100%  103%  106%  108%  109%  109%
Tier 5:    22%   66%   85%   95%  102%  107%  110%  113%  115%  117%  118%
Tier 9:    22%   67%   87%   98%  105%  110%  113%  116%  118%  120%  120%
```

**XTC validation**:
| XTC Value | Matrix Match | Error |
|-----------|--------------|-------|
| 64.0% | Tier 2, Level A (64%) | 0.0% |
| 80.7% | Tier 1, Level B (81%) | 0.3% |
| 103.1% | Tier 0, Level F (103%) | 0.1% |

### Implications

1. **Highest confidence data**: This is our most reliable parameter set
2. **Exact values matter**: Small differences affect production calculations
3. **Expert efficiency**: Max 120% (Tier 9, Level J) confirmed

### References
- `prosim/config/defaults.py:TRAINING_MATRIX`
- `docs/verification_guide.md` Section 2
- `prosim/engine/accuracy_benchmark.py:benchmark_training_matrix()`

---

## 8. week1.txt is Rosetta Stone for REPT Format

**Date Discovered**: December 2025

**Category**: Format Understanding

### The Discovery

The file `week1.txt` is a **human-readable version** of a REPT file, containing identical data in a formatted layout. This allowed us to definitively decode the REPT file format.

### Evidence

**REPT file** (machine-readable):
```
14            2             0             4             5
2413.50       1200.00       ...
```

**week1.txt** (human-readable):
```
======================== PROSIM III WEEKLY REPORT ========================

WEEK: 1                                    COMPANY: 1

---------------------------- COST SUMMARY ------------------------------
                           PRODUCT                               WEEKLY
COST ITEM              X         Y         Z        TOTAL        TOTAL
```

**Field-by-field match confirmed** between REPT14.DAT and report.doc (Word version)

### Implications

1. **Format decoded**: Can write authentic REPT output
2. **Authentic display**: CLI uses original 2004 format
3. **Two formats exist**: Machine-readable (.DAT) and human-readable (.txt)

### References
- `prosim/io/rept_parser.py:write_rept_human_readable()`
- `archive/data/week1.txt`
- `IMPLEMENTATION_PLAN.md` "Authentic Report Format Verification"

---

## 9. Game Efficiency vs Operator Efficiency

**Date Discovered**: December 2025

**Category**: Terminology Clarification

### The Discovery

PROSIM uses "efficiency" for **two completely different metrics**:

| Metric | Formula | Range | Meaning |
|--------|---------|-------|---------|
| **Operator Efficiency** | Output ÷ Expected | 50-120% | Worker productivity |
| **Game Efficiency** | Standard Cost ÷ Actual Cost | 70-130%+ | Company performance |

### Evidence

**Spreadsheet Week 16 data** showed:
- Operators at 99-132% efficiency (output-based)
- Z' Production = 0 (shutdown strategy)
- High game efficiency despite no production

**This reveals the "shutdown strategy"**:
1. Build inventory before final shipping week
2. Cut production to minimum
3. Ship from inventory
4. Actual costs drop → Game efficiency spikes

### Implications

1. **Don't confuse metrics**: Operator efficiency ≠ Game efficiency
2. **Strategic insight**: Shutdown strategy exploits cost-based efficiency formula
3. **End-game behavior**: Efficiency >100% is achievable and intended

### References
- `docs/algorithms.md` Section 5 "Game Performance Efficiency"
- `IMPLEMENTATION_PLAN.md` "Game Efficiency Formula" section

---

## 10. Nelson.xls Structure Reconstructed

**Date Discovered**: December 2025

**Category**: Data Recovery

### The Discovery

The lost external file `Nelson.xls` was **reconstructed** from formula analysis in ProsimTable.xls, allowing the spreadsheet to function again.

### Evidence

**Formulas revealed required structure**:
```excel
=DGET($A$6:$E$34,$C$6,$J21:$J22)  -- needs columns A-E with headers in row 6
=DSUM($G$34:$H$62,$H$34,$I21:$I22) -- needs columns G-H starting row 34
```

**Required data derived from**:
- Existing values visible in Operators tab
- DGET lookup criteria patterns
- Training accumulator logic

### Reconstructed File

**Sheet1 structure**:
```
A2:B30   - Operator base lookup (op, base)
A34:E62  - Training accumulator (op, week, days_wo, days_with, op)
G34:H62  - Trained weeks accumulator (op, trained)
```

**Seed data from spreadsheet**:
- Op 3: 18 days without supervisor, 9 days with
- Op 7: 21 days without, 9 days with
- Op 26: 15 days without, 5 days with
- (etc.)

### Implications

1. **Spreadsheet functional**: ProsimTable.xls now works with reconstructed Nelson.xls
2. **Path update needed**: Must update Excel links from `C:\Operators\Nelson.xls`
3. **Other files may exist**: Andy.xls, Shorty.xls referenced but not found

### References
- `archive/spreadsheets/Nelson.xls` (reconstructed)
- `CLAUDE.md` "Nelson.xls - External Data Dependency"
- `docs/algorithms.md` "Appendix A" sections on external dependencies

---

## 11. ProsimTable.xls Evolution Traced

**Date Discovered**: December 2025

**Category**: Archive Insight

### The Discovery

The main reverse-engineering spreadsheet `ProsimTable.xls` evolved through **four tracked versions** over 2 months (May-July 2004). A recovered floppy disk file (`C5A53900`) was identified as the earliest version.

### Evidence

**All versions share identical creation metadata**:
- Created: Fri May 14 23:55:43 2004
- Author: Shorty
- Last Saved By: Nelson de Wilt

**Version progression** (by save date):

| Version | File | Save Date | Size | Sheets |
|---------|------|-----------|------|--------|
| v1 | `A/week 2/C5A53900` | May 20, 2004 | 98 KB | 5 |
| v2 | `A/week 2/ProsimTable(Nelson).xls` | May 25, 2004 | 105 KB | 9 |
| v3 | `ProsimTable(Week3).xls` | Jun 5, 2004 | 133 KB | 11 |
| v4 | `ProsimTable.xls` | Jul 13, 2004 | 180 KB | 11 |

**Sheet evolution**:
```
v1 (May 20):  Sheet1, Entry, Results, Operators, Data
v2 (May 25):  + Graph, Cost, Forcasting, Sheet2
v3 (Jun 5):   + Week Sumary, Weekly Planing, Eff
v4 (Jul 13):  + DECS14 (final structure)
```

**C5A53900 identification**:
- Filename is Windows recovered file pattern (FAT filesystem)
- `BOOTEX.LOG` in same folder confirms floppy disk check
- Content structure matches later ProsimTable versions exactly
- Excel metadata links it to the lineage

**XTC files obtained later (Summer 2005)**:
- `prosim.xtc` and `prosim1.xtc` were obtained from Professor Rourke during a **Summer 2005 senior project** - an earlier reconstruction attempt with Shorty and one other student
- The May 2004 dates in the files reflect when the *games were played*, not when files were obtained
- Their binary format was **never decoded** until December 2025
- All 2004 spreadsheet analysis was done purely from REPT/DECS output observation, without these files

### Implications

1. **Shorty started the analysis**: Created the spreadsheet, passed to Nelson
2. **54 days of work**: Active reverse-engineering May 20 - July 13, 2004 (7 weeks, 5 days)
3. **Incremental discovery**: New tabs added as more PROSIM mechanics understood
4. **Collaboration evidence**: Spreadsheet passed between students via floppy disk
5. **Archive completeness**: We now have full development history
6. **No "answer key" used**: XTC files with hidden stats weren't obtained until a year later
7. **This is the third attempt**: 2004 (class), 2005 (senior project), 2025 (current reconstruction)

### References
- `Prosim/ARCHIVE_MANIFEST.md` "ProsimTable.xls Evolution" section
- `archive/spreadsheets/ProsimTable.xls` (final)
- `Prosim/A/week 2/C5A53900` (earliest, recoverable with .xls extension)

---

## Future Discoveries Needed

### High Priority

1. **XTC Float2 meaning**: What does the second float represent?
2. **Machine repair probability**: Exact formula and maintenance budget effect
3. **Starting company state**: What are Week 0 values?

### Medium Priority

4. **Hired operator generation**: How are stats assigned to operators 10+?
5. **Training progression**: Exact weeks required per training level
6. **Demand generation seed**: How is randomness seeded?

### Low Priority

7. **Carrying cost exact rates**: Parts and products per-unit costs
8. **Setup time edge cases**: Behavior when machine was idle

---

## Document History

| Date | Change |
|------|--------|
| Dec 2025 | Initial creation with 10 key discoveries |
| Dec 2025 | Added #11: ProsimTable.xls evolution traced via recovered floppy file |

---

*This document is part of the PROSIM Reconstruction Project forensic documentation suite. See also: `forensic_verification_status.md`, `verification_guide.md`, `xtc_verification_guide.md`.*
