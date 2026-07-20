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
| 12 | [PROSIM VII Doctoral Thesis Found (1992)](#12-prosim-vii-doctoral-thesis-found-1992) | Dec 2025 | Historical context |
| 13 | [Two Separate PROSIM Product Lines Identified](#13-two-separate-prosim-product-lines-identified) | Dec 2025 | **CRITICAL** - Changes project understanding |
| 14 | [XTC Format Fully Re-Analyzed](#14-xtc-format-fully-re-analyzed--same-game-tagged-grammar-float2-bounded) | Jul 2026 | Critical - Corrects #6; same-game saves; Float2 bounded |
| 15 | [XTC Packed Region Structure Decoded](#15-xtc-packed-region-structure-decoded) | Jul 2026 | Critical - The unread 95% of the saves has a mapped structure |
| 16 | [Departments, Deterministic Production, Event Flags](#16-departments-deterministic-production-event-flags) | Jul 2026 | Critical - Corrects f3/f4 model; 11 operators; deterministic weekly output |
| 17 | [Spreadsheet Prediction Accuracy Quantified](#17-spreadsheet-prediction-accuracy-quantified) | Jul 2026 | Important - 2004 model fidelity exact; DECS14↔REPT14 matched pair found |

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

> **UPDATE (Jul 2026)**: See Discovery #14 — a full re-analysis corrected
> several claims below. Byte 9 is the **week number**, not operator count
> (the game never had 13 operators). Byte 44 is NOT a week counter. 0x15 is
> a record *tag*, not a delimiter, and the files are same-game saves whose
> operator log grows in shipping-period blocks, not weekly snapshots.

**File structure decoded** (as corrected by Discovery #14):
```
Header (87 bytes):
  Byte 9:  Week number (9 / 13)
  Byte 40: Max simulation weeks (24)
  Byte 44: Unknown (NOT a week counter)

Body records, tag byte + payload:
  0x15 + [Float1:4][Float2:4][Float3:4][Float4:4]  (operator record)
  0x12 + [~2.80:4][~2.80:4]                        (period separator)
```

**Float1 values correlate with proficiency** (scale factor 1.088):
```
XTC Float1 × 1.088 ≈ Derived Proficiency

1.0312 × 1.088 = 1.122 → Op 3 (Expert)  ✓ EXACT MATCH
0.9667 × 1.088 = 1.052 → Op 1           ✓
0.6397 × 1.088 = 0.696 → Op 6           ✓
```

**File size indicates game progress**:
- prosim.xtc (18,963 bytes) = Week 9 save
- prosim1.xtc (29,088 bytes) = Week 13 save (same game, later point — see #14)
- File grows ~2,000-2,100 bytes per game week (packed log region)

### Implications

1. **New validation source**: Can verify proficiency model against binary data
2. **Growing log**: File grows as game progresses (shipping-period blocks, not weekly snapshots — see #14)
3. **Float2 partially resolved**: See Discovery #14 — a fixed per-operator efficiency/quality coefficient
4. **Instructor data**: These are from Professor Rourke's computer (instructor-side files)
5. **Not used in 2004**: All original reverse-engineering was done without this data - the training matrix and efficiency formulas were derived purely from REPT/DECS observation
6. **Obtained in 2005**: Files grabbed during senior project reconstruction attempt, sat undecoded for 20 years

### References
- `docs/xtc_verification_guide.md` (complete analysis)
- `docs/history.md` (historical context)
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

## 12. PROSIM VII Doctoral Thesis Found (1992)

**Date Discovered**: December 2025

**Category**: Academic Lineage / Historical Context

### The Discovery

The **1992 Master's Thesis** that created PROSIM VII was located - a 180-page academic document titled *"PROSIM VII: An Enhanced Production Simulation Model"* by **Louis Cadmon Alexander** at **Ohio University**. This establishes the complete academic lineage and reveals that the operator training/efficiency model was **NOT present in PROSIM VII**.

### Evidence

**Document metadata**:
- **Title**: PROSIM VII: An Enhanced Production Simulation Model
- **Author**: Louis Cadmon Alexander
- **Institution**: Ohio University, College of Engineering and Technology, Department of Industrial and Systems Engineering
- **Date**: August 1992
- **Advisor**: Dr. Ken Cutright
- **Source file**: `ohiou1171474745.rtf` (OCR conversion from PDF)

**PROSIM Version History** (documented in thesis):
| Version | Year | Platform | Author |
|---------|------|----------|--------|
| PROSIM V | 1971 | Mainframe/FORTRAN | Dr. Joe H. Mize, Auburn University |
| PROSIM VI | 1981 | Apple II Plus | Dr. Richard E. Ward, James C. Wright, WVU |
| PROSIM VII | 1992 | IBM PC/True Basic | Louis Cadmon Alexander, Ohio U |

**PROSIM VII Features** (documented in thesis):
- Stochastic process times (uniform, normal, exponential, gamma)
- Machine breakdown with exponential interbreakdown times
- Repair times (deterministic or stochastic)
- Defective incoming material and outgoing products
- Quality control plan (100% inspection vs sampling)
- Up to 25 work stations, 75 stock numbers, 5 work station tours

**Critical Negative Finding**:
The thesis contains **zero mentions** of:
- "efficiency" (as we use it for operators)
- "proficiency"
- "training" (for operators)
- "operator" training/skill development

This proves the **two-component operator efficiency model** we see in PROSIM III (2004) was **added after 1992** in a subsequent version.

### Thesis Chapter Structure

| Chapter | Content |
|---------|---------|
| I | Introduction - Background of project |
| II | Background of Production Control Education |
| III | Literature Review - Including detailed PROSIM V/VI documentation |
| IV | Statement of the Problem |
| V | Solution Methodology - **The enhancement formulas** |
| VI | Discussion of Results - Validation |
| VII | Conclusions and Recommendations |
| Appendix A | Example Problem without enhancements |
| Appendix B | Example Problem with enhancements |

### Key Formulas from Thesis

**Machine Breakdown** (Section 5.2):
- Interbreakdown times: Exponential distribution (based on busy time)
- Repair times: Uniform, normal, exponential, or gamma (administrator choice)

**Quality Control** (Section 5.4):
- 100% inspection OR lot sampling OR no inspection
- Defective percentage for each product (uniform random test)
- Penalty cost for bad products leaving factory

**Cost Structure**:
- Idle time costs (man + machine)
- Labor costs per shift (shift 1, 2, 3, overtime)
- Setup times, process times
- Carrying costs, order costs
- Out-of-stock costs

### Implications

> **UPDATE (Dec 2025)**: See Discovery #13 - PROSIM VII (Mize lineage) is a **completely separate product** from PROSIM III (Greenlaw lineage). The thesis below documents a different simulation system.

1. **NOT our ancestor**: PROSIM VII (Mize/Ohio U) is unrelated to PROSIM III (Greenlaw/commercial)
2. **Historical value**: Documents academic simulation development 1971-1992
3. **Architecture comparison**: Different approach - stock numbers vs operators
4. **Quality system different**: 1992 Mize version used inspection/sampling; Greenlaw version uses quality budget

### Historical Timeline (Mize Academic Lineage Only)

```
1971 - PROSIM V created (Auburn, mainframe) - Dr. Joe H. Mize
1981 - PROSIM VI (WVU, Apple II)
1992 - PROSIM VII thesis (Ohio U, IBM PC)
      ↓
    [This lineage does NOT lead to PROSIM III]
```

### References
- `docs/prosim_vii_thesis_1992.txt` (full extracted text, 180k chars)
- `Prosim/ohiou1171474745.rtf` (original OCR file, 2.8MB)
- `CLAUDE.md` PROSIM Archive documentation

---

## 13. Two Separate PROSIM Product Lines Identified

**Date Discovered**: December 2025

**Category**: **CRITICAL** - Foundational Project Understanding

### The Discovery

There are **TWO completely separate and unrelated PROSIM product lines** with similar names:

| Product Line | Our Target? | Origin | Focus |
|--------------|-------------|--------|-------|
| **Greenlaw PROSIM** | **YES** | Commercial (1969) | Operations Management |
| **Mize PROSIM** | No | Academic (1971) | Production Control |

**PROSIM III for Windows** (our reconstruction target) is part of the **Greenlaw commercial lineage**, NOT the Mize academic lineage documented in the 1992 thesis.

### Evidence

**Course materials from MGMT475 (Summer 2003)**:
- Presentation slide shows "PROSIM III - A Production Management Simulation"
- Same branding and graphics as the commercial textbook

**Amazon product listing**:
- **Title**: "Prosim III for Windows: A Production Management Simulation"
- **Authors**: Chao-Hsien Chu, Michael P. Hottenstein, Paul S. Greenlaw
- **Publisher**: Richard D. Irwin (McGraw-Hill imprint)
- **ISBN-10**: 0256214352
- **ISBN-13**: 978-0256214352
- **Edition**: Third Edition (1996)
- **Length**: 224 pages (textbook + software)

**Paul S. Greenlaw background** (from obituary):
- Pioneer in educational business simulations
- Co-authored PROSIM 1st edition in **1969** with Michael P. Hottenstein
- Also created MARKSIM, FINANSIM simulations
- Published through Prentice-Hall, Harper & Row, Irwin

### The Two Product Lines

#### Greenlaw Commercial Lineage (OUR TARGET)

| Version | Year | Authors | Publisher |
|---------|------|---------|-----------|
| **PROSIM** (1st ed) | **1969** | Greenlaw & Hottenstein | Harper & Row |
| PROSIM (2nd ed) | ~1979 | Greenlaw & Hottenstein | Harper & Row |
| **PROSIM III for Windows** | **1996** | Chu, Hottenstein, Greenlaw | Irwin/McGraw-Hill |

- **Commercial textbook + software bundle**
- Windows-based graphical interface
- Operator-focused simulation with training system
- Used at multiple universities (Wentworth, Ohio U, others)
- 224-page textbook included with software

#### Mize Academic Lineage (NOT our target)

| Version | Year | Author | Institution |
|---------|------|--------|-------------|
| PROSIM V | 1971 | Dr. Joe H. Mize | Auburn University |
| PROSIM VI | 1981 | Ward & Wright | West Virginia University |
| PROSIM VII | 1992 | Louis C. Alexander | Ohio University |

- **Academic research project** (thesis-based)
- Stock number / work station focused
- FORTRAN → Apple II → IBM PC/True BASIC
- Quality via inspection/sampling (not quality budget)
- No operator training/efficiency system

### Implications

1. **The 1992 thesis is NOT our ancestor** - Different product entirely
2. **Textbook may contain all formulas** - The 224-page PROSIM III manual likely documents everything we've been reverse-engineering
3. **Book ordered from Amazon** - ISBN 978-0256214352 ($44, temporarily out of stock)
4. **Author potentially contactable** - Chao-Hsien Chu appears to be at SMU Singapore
5. **Explains naming confusion** - "III" = Third Edition (1996), not related to "VII" = 7th academic version (1992)
6. **Commercial distribution** - Explains why same software used at Wentworth (MA) and Ohio University

### Why the Confusion Occurred

1. Both products named "PROSIM"
2. Both used for production/operations management education
3. Both used at Ohio University at different times
4. Similar publication timeframes (1990s)
5. The 1992 thesis was found in Ohio University repository, same institution where PROSIM III was used

### Historical Timeline (CORRECTED)

```
GREENLAW LINEAGE (Commercial) - OUR TARGET
==========================================
1969 - PROSIM 1st Edition (Greenlaw & Hottenstein, Harper & Row)
1979 - PROSIM 2nd Edition (Harper & Row)
1996 - PROSIM III for Windows (Chu, Hottenstein, Greenlaw, Irwin)
  ↓
2003 - Used at Wentworth Institute (MGMT475 Summer 2003)
2004 - Used at Ohio University (our archive files from this course)
  ↓
2025 - This reconstruction project


MIZE LINEAGE (Academic) - UNRELATED
===================================
1971 - PROSIM V (Mize, Auburn, mainframe)
1981 - PROSIM VI (WVU, Apple II)
1992 - PROSIM VII (Ohio U, IBM PC)
  ↓
[Different product, not our ancestor]
```

### Action Items

1. **Await PROSIM III textbook** - Ordered from Amazon, may contain complete documentation
2. **Contact Michael P. Hottenstein** - Professor Emeritus, Penn State Smeal College of Business (living co-author, best prospect for materials)
3. **Contact Dr. William D. Biggs** - Arcadia University, ABSEL Fellow (Greenlaw's doctoral student)
4. **Search WorldCat for Instructor's Manual** - ISBN 978-0256214369 (194 pages, detailed algorithms)
5. **Penn State Archives inquiry** - Special Collections may hold faculty papers
6. **Continue reverse-engineering** - Textbook delivery uncertain; maintain current approach

### Additional Research Findings (Dec 2025)

**Research report**: `docs/PROSIM - Tracking a lost educational simulation from 1968.md` (also available as PDF)

**Version history refined**:
- Chu joined the project in **1991** (2nd edition), not 1996
- Springer citation confirms: "Greenlaw, P.S., Hottenstein, M.P. and Chu, Chao-Hsien (1991) PROSIM, A Production Management Simulation. 2nd Ed., Harper Collins"

**Academic sources discovered**:
- ABSEL Proceedings archives (https://absel-ojs-ttu.tdl.org/absel/issue/archive)
- Johnson & Hendrick (1975): "OMSIM" paper references PROSIM V
- Biggs (1986): "Computerized Business Management Simulations" bibliography
- Greenlaw's 1962 foundational text: *Business Simulation in Industrial and University Education*

**Software preservation status**: Confirmed not preserved in any major archive (Internet Archive, WinWorld, Vetusware, etc.)

### References
- Amazon: https://www.amazon.com/Prosim-Windows-Production-Management-Simulation/dp/0256214360
- Paul S. Greenlaw obituary (2005): https://www.legacy.com/us/obituaries/centredaily/name/paul-greenlaw-obituary?id=26678227
- Chao-Hsien Chu profile: https://www.smu.edu.sg/faculty/profile/26277/CHU-Chao-Hsien
- Course presentation slide: `Prosim/475ProSim.ppt` (MGMT475 Summer 2003)
- ABSEL proceedings: https://absel-ojs-ttu.tdl.org/absel/issue/archive
- Springer citation: https://link.springer.com/chapter/10.1007/978-0-387-35089-9_17
- Research report: `docs/PROSIM - Tracking a lost educational simulation from 1968.pdf`

---

## 14. XTC Format Fully Re-Analyzed — Same Game, Tagged Grammar, Float2 Bounded

**Date Discovered**: July 2026

**Category**: Formula Correction / Format Understanding

### The Discovery

A systematic multi-agent re-analysis of `prosim.xtc` / `prosim1.xtc` (byte-accounting parse, cross-file diffing, REPT cross-reference) corrected several prior claims and established: **both files are saves of the SAME game** at weeks 9 and 13, the operator log is a **growing tagged record structure** (not weekly snapshots or a fixed table), and **Float2 is a fixed per-operator coefficient** in the 0.55–0.68 band (one outlier ≈1.01), complementary to Float1.

### Evidence

**Corrected file layout** (verified by exhaustive byte-accounting parse; scripts in `analysis/xtc/`):

| Region | prosim.xtc | prosim1.xtc | Content |
|--------|-----------|-------------|---------|
| Preamble | 0–16 | 0–16 | Byte 9 = week number; unknown counters at bytes 1-2, 6 (+5/wk), 8 (+26/wk) |
| Header TLV | 16–78 | 16–78 | ASCII-digit-tagged records ('5','2','3','8'); '8' holds a +Inf placeholder |
| Operator log | 78–912 | 78–1355 | `0x15`+4×float32 operator records; `0x12` period separators |
| Packed region | 912–EOF | 1355–EOF | >95% of file; high-entropy per-week log, unparsed (see below) |

**Key corrections to prior claims**:

| Prior claim | Verdict | Evidence |
|-------------|---------|----------|
| Byte 9 = number of operators | **REFUTED** | REPT12-14 rosters show 8-9 active operators, never 13. Byte 9 = week number; week and claimed headcount coincidentally matched (9/9, 13/13) |
| Byte 44 = week counter | **REFUTED** | Reads 9 (wk9 file) and 8 (wk13 file) |
| Byte 40 = max weeks (24) | **CONFIRMED** | 0x18 in a byte-identical static config block in both files |
| 0x15 = record delimiter | **CORRECTED** | 0x15 is a record *tag* (17-byte records); irregular gaps were 0x15 bytes inside float mantissas plus interleaved 9-byte `0x12` separator records |
| Files = weekly snapshots | **REFUTED** | Operator log has 48 records in runs [45,3] (wk9) vs 73 in runs [44,7,9,13] (wk13) — blocks track ~4-week shipping periods, not weeks |
| Float1 × 1.088 = proficiency | **WEAKENED** | Exact only for Op 3 (1.0312×1.088=1.122); does not reproduce the other documented proficiencies. Float1 is a fixed proficiency-*like* per-operator constant |
| Two files from different games | **REFUTED** | All 11 (f1,f2) identities appear byte-identically in both files, and the lifetime accumulator (Float4) advances for every operator wk9→wk13 — same game, later save |

**New understanding of the four floats** (moderate confidence;
> **Float3/Float4 interpretations below were superseded by Discovery #16** —
> f3 is a global running counter and f4 a group-scoped aggregate):

- **Float1**: fixed per-operator proficiency/speed coefficient (hire constant, does not change with training)
- **Float2**: fixed per-operator second coefficient, range 0.549–0.678 (outlier 1.0145). Not a training-matrix cell; best-fit rationals share no common denominator, so it is a *computed* value stored at hire. Its band coincides with PROSIM's reported "Percent of Efficiency" range (54–65% in REPT data). Interpretation: the quality/yield axis of the two-component operator model. Exact formula still open.
- **Float3**: period-to-date accumulator — resets every ~4 weeks (sawtooth visible when ordered by Float4); bounded ~16–18k in both saves
- **Float4**: lifetime cumulative accumulator — grows monotonically for every operator between the two saves (e.g. expert: 12,578 → 22,775 ≈ 1,752/week)
- One Float1 value (0.818824) is shared by **two different operators** with different Float2 values (0.549020 / 0.583333) — (f1,f2) is the identity, not f1 alone
- Records group into department teams (4 Parts + 5 Assembly slots); `f1=f2≈2.80` records are idle-slot sentinels, present at week 9 and filled by week 13

**The unparsed 95%**: the packed region grows ~2,000–2,100 bytes/game-week in both files, resists standard decodings (not fixed-width bit-packing, RLE, or deflate), but contains a 66-byte block repeated identically 3×/7× and a 414-byte block 4×/6× (counts scale with weeks), each preceded by the same 16-byte prefix and followed by a monotonically increasing counter — consistent with a custom-packed per-week state log. This is now the largest untapped data source in the archive.

### Implications

1. **The instructor game's operator history is recoverable**: full extraction with block structure is in `analysis/xtc/synth_full_table.csv` (125 records)
2. **Float2 hypothesis space narrowed**: it is fixed-at-hire and efficiency-band-valued; Hypotheses A/B from `xtc_verification_guide.md` (tier factor / training level) are effectively dead — it does not change across 4 game weeks
3. **Shipping-period (~4-week month) structure exists in the engine** — matches the "Demand This Month" concept in reports and should inform our simulation's month handling
4. **Validation caution**: any prior analysis that used the naive 0x15-scan extraction (value-filtered float pairs) sampled an incomplete record set
5. **Next unlock is the packed region**: decoding it would likely yield authoritative per-week state for 13 weeks of a real game — the matched DECS+REPT-equivalent data the project has been missing

### References

- `docs/xtc_verification_guide.md` (updated with corrected grammar)
- `analysis/xtc/` (all analysis scripts + `synth_full_table.csv`, `quads_history.csv`)
- `archive/data/prosim.xtc`, `archive/data/prosim1.xtc`

---

## 15. XTC Packed Region Structure Decoded

**Date Discovered**: July 2026

**Category**: Format Understanding / New Data Source

### The Discovery

The high-entropy "packed region" (>95% of each XTC file, flagged as undecoded in Discovery #14) is a **numbered sequence of per-entity state records aligned 1:1 with the operator log**. Each record's payload is an identity-keyed template with a dynamic queue-like suffix and an event-tail marker. The macro structure is now fully mapped; payload internals are partially decoded.

### Evidence

**Record framing (high confidence)**: Records are marked `[n][0x0a]` with n incrementing. Complete gap-free chains: prosim.xtc n=1–49 (first marker at offset 1350), prosim1.xtc n=1–76 (first at 2111). These counts equal the body-log entry counts exactly (48 `0x15` + 1 `0x12` = 49; 73 + 3 = 76), and the alignment is verified: stripping the 2-byte marker, identical payload contents map to the same body (f1,f2) identity with a **100% match rate** (54/54 same-content pairs in file a, 179/179 in file b).

**Identity-keyed templates (high confidence)**: Only ~12 distinct identities exist (consistent with 9 operator/machine slots — 4 Parts + 5 Assembly — plus 3 products). The same identity produces byte-identical payloads across different weeks and different f3/f4 accumulator values — the payload does NOT encode the body floats (searched; never found). Payload sizes cluster per identity (88–414 bytes core).

**Payload anatomy (medium-high confidence)**:
```
[n][0x0a]                          record marker
[varint][varint]                   two LEB128 constants per identity
                                   (e.g. 410/327, 304/212 — meaning unknown)
[0x86 or 0x87]                     tag byte
[u16be][u16be]                     paired values, usually consecutive (+1)
[dense body...]                    identity template (repeats when unchanged)
[transient suffix]                 grows/shrinks between occurrences (queue)
[event tail][0x17]                 decoration tokens 0x0d/0x1a/0x09,
                                   prepended per event; 0x17 = sentinel
```

**Dynamics (from consecutive same-identity diffs)**:
- Most identities: stable core, changes are pure append/remove at the end — e.g. one identity goes 248 → 927 → back to exactly 248 bytes (enqueue/dequeue behavior)
- One identity oscillates between exactly two full templates (307 ↔ 339 bytes) repeatedly — alternating-assignment behavior (machine/product changeover hypothesis)
- Occasional transient spikes (637–2,405 bytes) appear and vanish — discrete events
- The `f1=f2≈2.80` identities carry genuinely variable-length payloads with negative f3 — best hypothesis: **product records (X/Y/Z)** with order/demand queues

**Separator records**: all four body `0x12` separators (across both files) carry the event-tail decoration `0x0d _ 0x1a _ 0x09 _ 0x17` at payload end — a deterministic structural signature.

**Cross-file behavior (important)**: file b is a **full re-serialization**, not an append of file a — only 2/49 record positions have identical payloads (coincidence), and body identities at the same n match only ~8% between files. Record number n is a within-save key only. The body log order is therefore NOT a stable chronological history across saves.

**Preamble**: 438 bytes (a) / 756 bytes (b) before record 1 remain undecoded — dense varint-like data, not a sparse bitfield; b's does not contain a's.

### Implications

1. **The packed region is no longer a black box** — record boundaries, entity attribution, and change events are all extractable (`analysis/xtc/map_alignment.csv`)
2. **Per-entity event history is recoverable in principle**: change points in an identity's template sequence mark discrete game events (training/reassignment/repair candidates); the transient suffixes are queues whose contents are the next decode target
3. **The 9-slot + 3-product structure** visible here reframes the "operator records" as likely machine/slot records with assigned-operator constants — relevant to how the reconstruction models assignments
4. **The re-serialization finding constrains save semantics**: PROSIM rebuilt the whole state table each save (with dynamic ordering), so cross-save byte comparisons are only meaningful per-identity, never positional
5. Remaining unknowns: queue/suffix contents, the preamble, the two per-identity head varints, the event-tail token semantics, and the cross-save ordering rule

### References

- `docs/xtc_verification_guide.md` (packed-region section updated)
- `analysis/xtc/` — `lead_tiling.py`, `map_*.py` + `map_alignment.csv`, `pay_*.py`
- Discovery #14 (grammar and float model this builds on)

---

## 16. Departments, Deterministic Production, Event Flags

**Date Discovered**: July 2026 (round 2 of the packed-region analysis)

**Category**: Core Mechanic / Formula Correction

### The Discovery

Round two of the XTC analysis decoded the department encoding, corrected the Float3/Float4 model from Discovery #14, established that there are **11 operator identities** (not 10), and — most significantly — showed that **weekly production is deterministic given the crew configuration**: the same crew produces byte-identical production deltas in different weeks and even across the two save files.

### Evidence

**Department tag byte (high confidence)**: each packed payload carries a tag byte after its two head varints: `0x87` for exactly 4 identities, `0x86` for exactly 5 — matching `parts_machines=4` / `assembly_machines=5` in the engine config. Two further identities use variant tags `0x82`/`0x84` with much smaller payloads and out-of-band field values — best interpreted as **hired operators** with a different record scheme (unconfirmed).

**11 identities, not 10**: two different operators share the exact same Float1 (0.818824) but differ in Float2 (0.583333 vs 0.549020) and in every packed-record constant. Any analysis keying identity on f1 alone conflates them. Corrected table: `analysis/xtc/c2_constants_corrected.csv`.

**Float3/Float4 corrected** (supersedes #14's verdicts c and d):
- **Float3 is a GLOBAL running counter**, not per-operator: it increases monotonically across *consecutive log records regardless of identity* (~300–600 per record), with sawtooth resets. Same-identity records within one group show f3 values from the shared global sequence.
- **Float4 is a group-scoped aggregate**: nearly constant (±few %) across each run of consecutive records, then jumps to a new plateau. Plateaus are NOT monotonic (e.g. 9,200 → 2,500) — **not** a lifetime accumulator. Groups ≈ calendar buckets (likely week × department crew).

**Deterministic production signatures (high confidence, the headline)**: segmenting the log by f4 plateaus yields crew groups whose *identity sequence and exact f3 delta sequence repeat*:
- prosim1.xtc groups n=1–7 and n=23–29: same crew `ID02,ID09,ID03b,ID06,ID10,ID09,ID02`, same deltas `+416,+479,+487,+295,+539,+484` — different weeks, identical amounts
- Three distinct crew signatures each appear twice in prosim1.xtc; one five-record signature (`+469,+467,+386,+515`) appears in **both files**
- Implication: whatever randomness PROSIM has, per-event operator production amounts are **deterministic functions of the crew configuration**

**Event flags, not counters (high confidence)**: the small payload-tail changes are additions/removals of complete 2-byte tokens (`0x0d/0x1a/0x09` + gap byte), and they are **reversible** — a token appears at one occurrence and disappears at a later one. These behave as independent boolean event flags (repair / training / assignment-state candidates), refining round one's "counter" guess.

**66-byte repeated block resolved**: all 10 occurrences map 1:1 onto identity ID04's payloads at the same internal offset, byte-identical across weeks and files — compiled-in per-operator constant data, consistent with the fixed `STARTING_OPERATOR_PROFILES`.

**Negative results (documented so they aren't retried)**:
- The two per-identity head varints (V1,V2) match **no** arithmetic function of f1/f2/rates/training-matrix values (exhaustive search, <2% tolerance, all-identity requirement)
- The dense payload interiors and the preamble are not plaintext numerics (no varint/float/int16 structure, entropy ~7.3 bits/byte) — but share an internal grammar: `[0x80–0x87][0xF8–0xFE]` sub-headers every ~20–90 bytes and nested `[value][0x0a]` delimiters. A decoding transform (XOR/delta/bit-level code) is still needed.
- The preamble uses the same queue grammar globally (5 segments at week 9 → 11 at week 13); candidate: order backlog / global event queue / RNG buffer

### Implications

1. **Reconstruction constraint**: per-event production amounts must be modeled as deterministic functions of crew configuration — no per-week noise in operator output
2. **The f3 delta table is directly harvestable** as ground-truth production quantities per (crew, slot) — usable for calibrating the output formula once slots are tied to operators/machines
3. **Department membership per operator is now known exactly** — including that the two "same-f1" operators sit in *different* departments
4. **Known-plaintext attack is now possible** on the dense payload interiors: we know each payload's week produced specific f3 deltas, giving target values to search for under candidate transforms
5. Any prior analysis keying operators on Float1 alone (including parts of #14) needs the 11-identity correction

### References

- `analysis/xtc/c2_constants_corrected.csv` (identity table), `c2_*.py`, `q2_*.py`, `ev_timeline*.py`, `q2_spans.csv`
- Discovery #14 (float model — verdicts c/d superseded), #15 (packed-region structure)

---

## 17. Spreadsheet Prediction Accuracy Quantified

**Date Discovered**: July 2026

**Category**: Validation / Historical Record

### The Discovery

The 2004 ProsimTable.xls forecasting pipeline was scored against actual game results wherever prediction/actual pairs exist in the archive. **The spreadsheet's production formula reproduces game output EXACTLY when inputs are correct** (`gross = productive_hours × standard_rate × efficiency` holds to the unit for all 8 REPT12 operators). Forward *forecast* accuracy was 89% per-operator / 93% on net output — the error came from coarse efficiency estimates, not wrong mechanics. The remembered "97% accuracy" is best explained as the **cumulative game-efficiency score** (0.949 at the last saved snapshot, trending toward ~0.97 in the final weeks) fusing with the genuine experience of exact model fidelity.

### Evidence

**Workbook pipeline** (all three versions): paste last week's report (`Entry`/`Sheet1`) → derive per-operator efficiency (`Operators`) → forecast the coming week (`Results`, `Weekly Planing`, `Forcasting`) → emit decision (`DECS14` tab).

**Snapshot dating**: Nelson.xls-era version (May 25) holds an exact paste of REPT12.DAT; Week3 version (Jun 5) plans game week 6; final version (Jul 13) plans game week 16 — which is why its forecasts cannot be scored against REPT14 (week 14).

**Accuracy table** (`analysis/xtc/v3_accuracy.csv`):

| Category | n | Mean accuracy | Note |
|---|---|---|---|
| Per-operator efficiency forecast | 9 | 89.3% | round estimates vs actual, systematic −6.8% under-forecast |
| Per-operator production forecast | 9 | 89.3% | proportional to efficiency estimate |
| Aggregate net output | — | 93.2% | errors partially cancel |
| Mechanics fidelity (known inputs) | 8 | **100.0%** | exact to the unit, REPT12 operators |
| Cumulative game efficiency (score, not forecast) | — | 94.9% | `Eff` tab, weeks 1–14; last weeks 1.288/1.282 |

**Corrections to prior records**:
- REPT14.DAT's roster is {1,2,3,4,5,6,7,18,26}; the "op 13" roster belongs to REPT13 (Shorty's)
- **DECS14.DAT is the actual submission that produced REPT14** — 9/9 match on operator, product, and scheduled hours. The archive DOES contain one matched decisions→report pair (partially easing Discovery #1's constraint; full end-to-end replay still needs the week-13 starting state)
- DECS14_week3.DAT is a different scenario (0/9 vs REPT14); DECS14_Aroot.DAT is a generic template identical to DECS12.txt except the week number
- The Results tab's daily "Should/Actual" columns are an internal what-if (a modeled raw-material-shortage factor of 0.7828), NOT recorded game actuals

### Implications

1. **The 2004 reverse-engineering was mechanically correct** — the production identity was nailed 20 years ago; only the efficiency *inputs* were estimates
2. **The reconstruction's validation target sharpens**: match the exact identity `gross = productive_hours × rate × efficiency` (already implemented) and treat 2004 forecast error as input uncertainty, not model error
3. **DECS14 + REPT14 form a usable constraint pair** for the simulation: given any candidate week-13 state, processing DECS14.DAT must produce REPT14.DAT
4. The "97%" memory is a fusion of a real ~95% efficiency score and real exact-fidelity experience — both flattering in substance, neither literally a 97% forecast metric

### References

- `analysis/xtc/v3_accuracy.csv`, `v3_*.py` scripts
- `archive/spreadsheets/ProsimTable*.xls` (three versions), `archive/data/REPT12-14.DAT`, `DECS14*.DAT`
- Discovery #1 (matched-pair constraint, partially eased), #9 (game efficiency vs operator efficiency — the same conflation trap)

---

## Future Discoveries Needed

### High Priority

1. **Decode XTC packed-record payload internals** - macro structure solved (see #15); remaining: queue/suffix contents, the 438/756-byte preamble, per-identity head varints, event-tail token semantics
2. **XTC Float2 exact formula**: Now known to be a fixed-at-hire efficiency-band coefficient (see #14); exact computation still open
3. **Machine repair probability**: Exact formula and maintenance budget effect
4. **Starting company state**: What are Week 0 values?
5. **PROSIM III Textbook** - Amazon order never arrived (as of Jul 2026); authors/archives not yet contacted (see #13 action items)

### Medium Priority

5. **Hired operator generation**: How are stats assigned to operators 10+?
6. **Training progression**: Exact weeks required per training level
7. **Demand generation seed**: How is randomness seeded?
8. **Contact Chao-Hsien Chu**: Author may have source code or documentation

### Low Priority

9. **Carrying cost exact rates**: Parts and products per-unit costs
10. **Setup time edge cases**: Behavior when machine was idle
11. **PROSIM I and II history**: What were the earlier Greenlaw editions like?

---

## Document History

| Date | Change |
|------|--------|
| Dec 2025 | Initial creation with 10 key discoveries |
| Dec 2025 | Added #11: ProsimTable.xls evolution traced via recovered floppy file |
| Dec 2025 | Added #12: PROSIM VII thesis (1992) found - establishes academic lineage |
| Dec 2025 | **MAJOR UPDATE** - Added #13: Two separate PROSIM product lines identified. Updated #12 to clarify Mize lineage is NOT our ancestor. PROSIM III (Greenlaw, 1969-1996) is our actual target. |
| Dec 2025 | Added research report findings to #13: Living co-author contact (Hottenstein), Instructor's Manual ISBN, ABSEL archives, academic citations. |
| Jul 2026 | Added #14: Full XTC re-analysis (multi-agent). Corrected #6 (byte 9 = week number, not operator count; log grows in shipping-period blocks, not weekly snapshots; same-game saves). Float2 bounded to fixed per-operator efficiency coefficient. |
| Jul 2026 | Added #15: Packed region structure decoded (numbered records 1:1 with body log, identity-keyed templates, queue suffixes, event tails). Archive sweep confirmed no third save / no original software; third DECS14 variant captured as `DECS14_Aroot.DAT`. |
| Jul 2026 | Added #16: Department tags, 11-identity correction, deterministic crew production signatures, reversible event flags, f3/f4 model corrected (supersedes #14 verdicts c/d). |
| Jul 2026 | Added #17: Spreadsheet prediction accuracy quantified (mechanics exact, forecasts 89-93%); DECS14↔REPT14 matched pair identified; REPT14 roster corrected. |

---

*This document is part of the PROSIM Reconstruction Project forensic documentation suite. See also: `forensic_verification_status.md`, `verification_guide.md`, `xtc_verification_guide.md`.*
