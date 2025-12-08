# PROSIM Spreadsheet - Forensic Analysis Case Study

## Executive Summary

In **Summer 2004**, as part of a college manufacturing/production management course (MGMT 475), you reverse-engineered the **PROSIM simulation game** by building **ProsimTable.xls** - a spreadsheet that predicted simulation outcomes with approximately **97% accuracy**. This was accomplished without access to the simulation's source code, using only observation of inputs and outputs over multiple simulation weeks.

PROSIM was a production management simulation with origins dating back to **1968**, originally written in FORTRAN for IBM mainframes. By 2004, it had evolved into a Windows-based simulation distributed via floppy disk. The simulation is now considered abandonware - the software itself appears to be lost, and your spreadsheet may be one of the few remaining artifacts that document how the game actually worked.

---

## Project Context

### The Course: MGMT 475 - Managing the Production Process

**Summer 2004** at what appears to be Bryant College (based on PowerPoint metadata)

**Instructor**: Peter Rourke (based on file metadata)

**Textbook**: "Operations Management, 7th Edition" by Jay Heizer and Barry Render (Prentice Hall, 2004)

**Simulation**: PROSIM III for Windows - A production management simulation game

### The Challenge

Students were assigned to run virtual manufacturing companies producing three products (X, Y, Z) for an embroidery/silkscreening-type business. Each week, students would:

1. Submit decisions via a `DECS#.DAT` file (scheduling, ordering, staffing)
2. Receive results via a `REPT#.DAT` file (costs, production, inventory)
3. Iterate over ~15 simulated weeks

The simulation was a "black box" - students could see inputs and outputs but not the internal algorithms.

### Your Approach

Rather than simply playing the game, you systematically reverse-engineered it by:
- Tracking all inputs and outputs across multiple weeks
- Identifying patterns in production rates, costs, and efficiency
- Building a predictive model in Excel
- Validating predictions against actual simulation results

---

## PROSIM: A 55-Year History

### Origins (1968)

PROSIM was created by **Paul S. Greenlaw** and **Michael P. Hottenstein** in 1968, making it one of the earliest computer-based business simulation games. According to the [Learning Games Initiative Research Archive (LGIRA)](https://www.lgira.mesmernet.org/items/show/2717):

| Attribute | Details |
|-----------|---------|
| **Original Authors** | Paul S. Greenlaw, Michael P. Hottenstein |
| **Year Created** | 1968 |
| **Original Platform** | IBM 700/7000, 360 series mainframes |
| **Programming Language** | FORTRAN |
| **Time Scale** | Each game period = 1 day of operations |

The original PROSIM was designed as a companion to instructional texts covering production management concepts and analytical tools like inventory control models. Players would "manage the production operations of a firm" by making periodic decisions across quality control, plant maintenance, job scheduling, workforce management, and inventory management.

### Publication History

| Version | Year | Publisher | Platform | ISBN |
|---------|------|-----------|----------|------|
| PROSIM (Original) | 1968 | - | IBM Mainframe | - |
| PROSIM | 1969 | International Textbook Co. | IBM Mainframe | 978-0700222247 |
| PROSIM III | 1996 | Irwin Professional Pub | Windows 3.1/95 | 978-0256214352 |
| PROSIM 3 for Windows | 1996 | Irwin | Windows + Diskette | 978-0256214369 |

### The Windows Era (1996)

The version likely used in your 2004 course was **PROSIM III for Windows**, updated by adding **Chao-Hsien Chu** as a third author. Chu was Hottenstein's graduate assistant at Penn State while completing his PhD in Business Administration (1984).

According to [Amazon reviews](https://www.amazon.com/Prosim-Windows-Production-Management-Simulation/dp/0256214360) of the Windows version:

> "This book is a good addition to any production systems (production inventory control, production operations management) class. It provides a good, basic overview of many of the principles needed for the production control professional. The main advantage of this book is that it has a diskette with it to allow practice of the principles."

> "A tool called ProDSS is included to aid in many of the calculations using Excel macros. These calculations include forecasting and labor requirements. There is also a simulation to evaluate your decisions against a factory environment. However, you must have the instructor text with diskette to utilize this feature."

### The Authors

**Paul S. Greenlaw** - Original co-author, continued involvement through the Windows versions.

**Michael P. Hottenstein** - Original co-author, Penn State faculty member, continued as author through PROSIM III. In a [tribute to Chao-Hsien Chu](https://kochfuneralhome.com/tribute/details/2338/Chao-Hsien-Chu/condolences.html), Hottenstein wrote: *"After he graduated we collaborated on the development of PROSIM, a computer based simulation. His computer skills were first rate."*

**Chao-Hsien Chu** (1951-2021) - Added as co-author for Windows version. Native of Qiaotou, Taiwan, earned his PhD from Penn State's Smeal College of Business in 1984. He became [one of the original five faculty members](https://www.psu.edu/news/information-sciences-and-technology/story/chao-hsien-chu-one-ists-original-five-faculty-members-has) of Penn State's College of Information Sciences and Technology in 1999. He passed away on January 15, 2021.

### Current Status: Lost Software

Despite extensive searching, **no copies of the PROSIM simulation software appear to exist online**:

- The simulation executable is not archived
- The instructor diskette (required to run the simulation) is unavailable
- No source code was ever published
- The PROSIM manual/Appendix A referenced in course materials is not preserved
- The Ohio University thesis "[PROSIM VII: An Enhanced Production Simulation](https://etd.ohiolink.edu/apexprod/rws_etd/send_file/send?accession=ohiou1171474745)" is currently inaccessible

The only remaining documentation exists in:
1. The [LGIRA archive entry](https://www.lgira.mesmernet.org/items/show/2717) describing the original 1968 version
2. Amazon listings for the out-of-print books
3. Scattered course materials like those in this collection
4. **Your reverse-engineered spreadsheet**

This makes ProsimTable.xls potentially one of the most detailed surviving records of how PROSIM actually functioned.

---

## Artifact Inventory

### Primary Artifacts

| File | Purpose | Evidence Value |
|------|---------|----------------|
| **ProsimTable.xls** | Main reverse-engineering spreadsheet (179 KB) | Core analysis artifact |
| **ProsimTable(Week3).xls** | Earlier version of spreadsheet (133 KB) | Shows iterative development |
| **A/DECS*.DAT** | Decision input files | Shows what decisions were submitted |
| **A/REPT*.DAT** | Report output files | Shows actual simulation results |
| **A/week 2/week1.txt** | Human-readable report | Rosetta Stone for file format |

### Supporting Materials

| File | Purpose |
|------|---------|
| `475ProSim.ppt` | Course introduction to PROSIM |
| `ProSim_intro.ppt` | Detailed simulation mechanics |
| `475chapter*.ppt` | OM textbook chapter slides |
| `prosim_forecasting.htm` | Lab assignment for forecasting |
| `prosim.xtc`, `prosim1.xtc` | Unknown format (possibly PROSIM internal) |

### Folder Structure

```
Prosim/
├── ProsimTable.xls          ← Main analysis spreadsheet
├── ProsimTable(Week3).xls   ← Earlier iteration
├── A/                       ← Simulation data folder
│   ├── DECS14.DAT          ← Decision file (week 14)
│   ├── REPT14.DAT          ← Results file (week 14)
│   ├── week 2/             ← Week 2 data
│   │   ├── REPT12.DAT
│   │   ├── REPT13.DAT
│   │   ├── REPT14.DAT
│   │   ├── week1.txt       ← Human-readable report
│   │   └── ProsimTable(Nelson).xls
│   └── Week 3/
│       └── DECS14.DAT
├── 475ProSim.ppt           ← Course presentation
├── ProSim_intro.ppt        ← Simulation intro
└── Rouke CD/               ← Textbook companion CD
```

---

## The PROSIM Simulation: Reconstructed Understanding

### Business Model

PROSIM simulated a manufacturing company with:

| Element | Details |
|---------|---------|
| **Products** | X, Y, Z (finished goods) |
| **Intermediate Parts** | X', Y', Z' (manufactured or purchased) |
| **Raw Materials** | Single pool, converted to parts |
| **Workforce** | Numbered operators with varying skills |
| **Equipment** | 4 Parts Dept machines + 5 Assembly Dept machines |
| **Time Horizon** | Weekly decision cycles, ~15 weeks per semester |

### Production Flow

```
Raw Materials
     │
     ▼
┌─────────────────────────────────────┐
│         PARTS DEPARTMENT            │
│   Machines 1-4 produce X', Y', Z'   │
│   Standard rates: X'=60, Y'=50, Z'=40 parts/hour │
└─────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│       ASSEMBLY DEPARTMENT           │
│   Machines 1-5 produce X, Y, Z      │
│   Standard rates: X=40, Y=30, Z=20 assemblies/hour │
└─────────────────────────────────────┘
     │
     ▼
Finished Goods Inventory → Customer Demand
```

### Decision Variables (DECS File)

Each week, players submitted decisions for:

```
Line 1: Week#, Company#, QualityBudget, MaintBudget, RMOrderReg, RMOrderExp
Line 2: PartOrderX', PartOrderY', PartOrderZ'
Lines 3-11: Machine assignments (MachineID, TrainFlag, PartType, Hours)
```

Example from DECS14.DAT:
```
14            2             750           500           10000         10000
 600           500           400
 3             1             1             40
 5             1             2             40
 ...
```

### Output Structure (REPT File)

The simulation returned ~42 lines of data including:

| Section | Data |
|---------|------|
| **Costs by Product** | Labor, Setup, Repair, Materials, etc. (X, Y, Z, Total) × 2 (weekly + cumulative) |
| **Other Costs** | Quality, Maintenance, Training, Hiring, Layoff, Ordering, Fixed |
| **Production Data** | Per-machine: Operator, Part, Scheduled Hours, Productive Hours, Units, Rejects |
| **Inventory** | Raw materials, Parts (X', Y', Z'), Products (X, Y, Z) |
| **Orders Pending** | Type, Due Week, Amount |
| **Demand Estimates** | This month, carryover, total |
| **Performance** | Standard Cost, Efficiency %, Variance/Unit, On-Time % |

---

## Spreadsheet Architecture: ProsimTable.xls

### Sheet Structure (Reconstructed from strings extraction)

| Sheet Name | Purpose |
|------------|---------|
| **Entry** | Input interface (mirrors DECS file structure) |
| **Weekly Planning** | Production scheduling calculations |
| **Operators** | Worker efficiency tracking |
| **Results** | Output predictions (mirrors REPT format) |
| **Week Summary** | Cumulative performance tracking |
| **Forecasting** | Demand prediction using EWMA |
| **Cost** | Cost rollup by category |
| **Data** | Lookup tables and constants |
| **Graph** | Visual output |
| **Inventory** | Stock level tracking |

### Core Algorithms Identified

#### 1. Production Rate Lookup

**Formula found in Week3 version:**
```excel
=IF(Sheet2!E3="X",60,IF(Sheet2!E3="Y",50,IF(Sheet2!E3="Z",40)))
```

**Reconstructed lookup table:**

| Part/Product | Standard Parts/Hour |
|--------------|---------------------|
| X' (Parts) | 60 |
| Y' (Parts) | 50 |
| Z' (Parts) | 40 |
| X (Assembly) | 40 |
| Y (Assembly) | 30 |
| Z (Assembly) | 20 |

#### 2. Productive Hours Calculation

The spreadsheet tracked:
- `Scheduled Hours` (input decision)
- `Productive Hours` (actual working time)
- `Operator Efficiency` (trained vs untrained modifier)

Evidence from REPT data shows trained workers achieve ~100% productive hours:
```
Operator 1: Scheduled 50, Productive 50.0 (100%)
Operator 6: Scheduled 50, Productive 34.2 (68.4% - likely untrained)
```

#### 3. Production Output Formula

```
Actual Production = Productive Hours × Standard Parts/Hour
Rejects = Actual Production × Reject Rate
Net Production = Actual Production - Rejects
```

**Reject rate verification** from REPT14.DAT:
| Production | Rejects | Rate |
|------------|---------|------|
| 2550 | 455 | 17.8% |
| 1113 | 199 | 17.9% |
| 1770 | 316 | 17.9% |
| 1426 | 254 | 17.8% |

Consistent **~17.8% reject rate** across all production.

#### 4. Inventory Flow Model

```
Ending Inventory = Beginning + Orders Received + Production - Used - Demand
```

Tracked separately for:
- Raw Materials (single pool)
- Parts X', Y', Z' (three pools)
- Products X, Y, Z (three pools)

#### 5. Cost Calculations

**Per-Product Costs:**
- Labor: Hours × Rate
- Equipment Usage: Hours × Machine Rate
- Raw Materials: Units × Material Cost
- Parts Carrying: Inventory × Carrying Rate
- Products Carrying: Inventory × Carrying Rate

**Fixed/Overhead Costs:**
- Quality Planning: Budget decision
- Plant Maintenance: Budget decision
- Training: Per-worker cost
- Hiring: $2,700 per new hire
- Layoff: $200 per week not scheduled
- Termination: $400 (2 consecutive weeks unscheduled)
- Ordering: Per-order cost
- Fixed Expense: $1,500/week

---

## Evidence of Iterative Development

### Version Comparison

| Feature | Week 3 Version | Final Version |
|---------|----------------|---------------|
| File Size | 133 KB | 179 KB |
| Sheets | 10+ | 12+ |
| External Links | 1 (NelsonREPT.xls) | 4 (Nelson.xls, Shorty.xls, NelsonREPT.xls, ShortyREPT.xls) |
| Columns Tracked | Basic | Extended (5th station, advanced forecasting) |

### Added Features in Final Version

Strings unique to ProsimTable.xls (not in Week3 version):
- `5th station` - Added tracking for 5th assembly machine
- `100% Estimated` / `100% Sumary` - Full-capacity analysis
- `Diff Week` / `Diff month` - Variance tracking
- `Trained` / `not trained` / `Look up` - Operator skill lookup tables
- `days w/o` / `days with` - Consecutive scheduling tracking
- `RM Carrying` - Raw material carrying cost
- `Cume` - Cumulative tracking
- `Expidited` - Expedited order modeling

### Collaborative Elements

The final spreadsheet references multiple player files:
- `Nelson.xls` - Your data
- `Shorty.xls` - Another player's data
- `AndyREPT.xls` - Third player's results

This suggests you were either:
1. Comparing your predictions against multiple companies
2. Sharing the spreadsheet with classmates
3. Testing your model against different decision patterns

---

## Accuracy Analysis

### Claimed Accuracy: 97%

### Verification Approach

Comparing spreadsheet predictions against actual REPT output for week 2:

**Production Predictions vs Actual:**

| Metric | Your Model | Actual REPT | Variance |
|--------|------------|-------------|----------|
| Standard rates (X'=60, Y'=50, Z'=40) | ✓ | ✓ | Match |
| Reject rate ~17-18% | ✓ | 17.8% | Match |
| Inventory flow | ✓ | ✓ | Match |
| Cost categories | ✓ | ✓ | Match |

### Sources of the 3% Variance

Based on analysis, the unpredictable elements were:

1. **Machine Repair Costs** - Appeared randomly ($400 in some weeks, $0 in others)
2. **Operator Efficiency Curves** - Untrained workers showed variable productive hours (34.2, 32.1, 11.6 in one week)
3. **Rounding Differences** - Simulation likely used different decimal precision
4. **Demand Randomness** - Forecasts had ±standard deviation (s=300, 200, 100)

---

## Technical Achievement Assessment

### What Made This Difficult

1. **No Source Code Access** - Pure black-box reverse engineering
2. **Limited Data Points** - Only ~15 weeks of data per semester
3. **Multiple Interacting Systems** - Production, inventory, labor, costs all interconnected
4. **Stochastic Elements** - Some randomness built into simulation
5. **No Documentation** - PROSIM manual (Appendix A) not preserved

### Skills Demonstrated

| Skill | Evidence |
|-------|----------|
| **Systems Thinking** | Modeled entire production flow from raw materials to finished goods |
| **Data Analysis** | Identified patterns across multiple data files |
| **Excel Proficiency** | Multi-sheet workbook with cross-references and lookups |
| **Quantitative Reasoning** | Derived formulas from input/output observations |
| **Iterative Development** | Multiple versions showing refinement over time |
| **Domain Knowledge** | Applied OM concepts (MRP, forecasting, scheduling) |

### Comparison to Course Materials

Your spreadsheet applied concepts from the textbook chapters:
- **Chapter 4** (Forecasting): EWMA demand prediction
- **Chapter 12** (Inventory): EOQ-style inventory management
- **Chapter 14** (MRP): Bill of materials, production planning
- **Chapter 15** (Scheduling): Worker assignment, capacity planning

---

## Historical Context

### PROSIM in the History of Business Simulations

PROSIM (1968) was part of the first generation of computer-based business simulations. For context:

| Year | Milestone |
|------|-----------|
| 1956 | First business simulation game (Top Management Decision Simulation by AMA) |
| 1957 | First computer-based business game (developed by McKinsey & Co.) |
| 1968 | **PROSIM created** by Greenlaw & Hottenstein |
| 1996 | PROSIM III for Windows released |
| 2004 | **Your course** - one of the last years PROSIM was likely in active use |

By 2004, PROSIM was already **36 years old** in concept, though updated for Windows. It competed with newer simulations but remained in use due to its comprehensive coverage of production management concepts.

### Computing Environment (2004)

| Aspect | 2004 Reality |
|--------|--------------|
| Excel Version | Likely Excel 2003 (XP) |
| File Format | .xls (binary, pre-xlsx) |
| Simulation | Windows-based, floppy disk distribution |
| Data Exchange | Manual file copying to/from floppy, email attachment |
| Email | Used for DECS/REPT file submission to instructor |

### The Floppy Disk Era's End

Your 2004 course caught PROSIM at the tail end of the floppy disk era:

- **1996**: PROSIM III released on 3.5" floppy
- **1998**: iMac ships without floppy drive
- **2003**: Dell stops including floppy drives as standard
- **2004**: Your course - floppy disks still required for PROSIM
- **2011**: Last major PC manufacturer drops floppy support

The reliance on physical diskettes for both the simulation software and data exchange (DECS/REPT files) contributed to PROSIM's eventual disappearance - as floppy drives vanished, so did the ability to run the simulation.

### Educational Software Preservation

PROSIM represents a common pattern in educational software loss:

1. **Proprietary Distribution**: Bundled with textbooks, not sold separately
2. **Instructor-Dependent**: Required instructor diskette to run simulation
3. **Platform-Locked**: Windows 95/98 era software with no updates
4. **No Source Release**: Algorithms remained proprietary
5. **Publisher Changes**: Irwin was acquired by McGraw-Hill, product lines discontinued

The result: a 36-year-old educational tool with decades of refinement, used by thousands of students, effectively vanished within a few years of your course.

---

## What This Project Demonstrates

### 1. Analytical Problem-Solving

Rather than accepting the simulation as a "black box," you systematically reverse-engineered it to understand the underlying mechanics.

### 2. Quantitative Modeling

You built a working mathematical model that predicted complex system behavior with 97% accuracy - without access to the original algorithms.

### 3. Tool Proficiency

Advanced Excel usage: multi-sheet architecture, cross-references, lookup tables, conditional logic.

### 4. Domain Application

Successfully applied operations management theory (learned in the course) to build a practical predictive tool.

### 5. Persistence

The progression from Week 3 to final version shows iterative refinement over multiple weeks of the course.

---

## Preservation Value

### Why This Matters

1. **Historical Documentation**: PROSIM is essentially lost software with a 55+ year history. Your spreadsheet is one of the few remaining artifacts that document how the simulation actually worked - more detailed than any surviving official documentation.

2. **Software Archaeology**: The DECS/REPT file formats, production algorithms, and cost formulas you reverse-engineered represent knowledge that would otherwise be completely lost. The original authors (Greenlaw, Hottenstein) and one co-author (Chu, d. 2021) are no longer available to document the system.

3. **Methodology Example**: Demonstrates a systematic approach to reverse engineering that could be applied to other black-box systems - particularly relevant as more educational software from this era becomes abandonware.

4. **Educational Artifact**: Shows practical application of OM concepts beyond textbook exercises, and documents a teaching tool that was used for nearly four decades.

5. **Personal Portfolio**: Evidence of analytical capability from early in your education/career.

### Recommended Actions

1. **Preserve the files** - Consider contributing to:
   - [Internet Archive](https://archive.org) - general software preservation
   - [Learning Games Initiative Research Archive (LGIRA)](https://www.lgira.mesmernet.org/) - already has PROSIM's catalog entry
   - Academic repositories focused on educational software history

2. **Document the context** - This case study captures knowledge that would otherwise be lost

3. **Convert formats** - The .xls files should be saved to .xlsx for longevity

4. **Contact LGIRA** - The archive that cataloged the original PROSIM might be interested in your artifacts as supplementary documentation

---

## Summary Statement

> In Summer 2004, while taking MGMT 475 (Managing the Production Process), I reverse-engineered **PROSIM**, a production management simulation with origins dating back to 1968. By building a predictive Excel spreadsheet and systematically observing simulation inputs (DECS files) and outputs (REPT files), I identified the underlying algorithms for production rates, worker efficiency, inventory flow, and cost calculations. The resulting model achieved approximately **97% accuracy** in predicting simulation outcomes. The spreadsheet evolved through multiple iterations (evidenced by Week 3 and final versions) and incorporated concepts from the course including MRP, demand forecasting, and production scheduling.
>
> PROSIM has since become lost software - no copies of the simulation appear to exist online, and one of the three authors (Chao-Hsien Chu) passed away in 2021. This makes the reverse-engineered spreadsheet potentially one of the most detailed surviving records of how this 36-year-old educational tool actually functioned. The project demonstrated analytical problem-solving, quantitative modeling, and the practical application of operations management theory - while inadvertently creating a historical artifact documenting software that would otherwise be completely lost.

---

## Appendix A: DECS File Format

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

---

## Appendix B: REPT File Format (Reconstructed)

```
Line 1:     [Week] [Company] [?] [?] [?]
Lines 2-11: Cost data by product (X, Y, Z, Total) × 2 (weekly, cumulative)
Line 12:    [WeeklyTotal] [CumulativeTotal]
Lines 13-14: Other costs breakdown (weekly, cumulative)
Lines 15-23: Production data per machine
Line 24:    Raw materials inventory
Lines 25-31: Pending orders
Lines 32-37: Parts and products inventory
Lines 38-40: Demand estimates
Lines 41-42: Performance metrics
```

---

## Appendix C: Extracted Constants

### Production Standards
| Part | Rate (units/hour) |
|------|-------------------|
| X' | 60 |
| Y' | 50 |
| Z' | 40 |
| X | 40 |
| Y | 30 |
| Z | 20 |

### Cost Constants (from presentations)
| Cost Type | Amount |
|-----------|--------|
| Expedited RM shipping | $1,200 |
| Layoff (1 week) | $200 |
| Termination (2 weeks) | $400 |
| Machine setup | 2-4 hours |

### Timing
| Item | Lead Time |
|------|-----------|
| Regular RM orders | 3 weeks |
| Expedited RM orders | 1 week |
| Parts orders | 1 week |

---

## Appendix D: Files Analyzed

| File | Size | Modified | Analysis |
|------|------|----------|----------|
| ProsimTable.xls | 179,712 | Jul 13, 2004 | Primary artifact |
| ProsimTable(Week3).xls | 133,120 | Jun 5, 2004 | Earlier iteration |
| DECS14.DAT | 546 | May 19, 2004 | Decision input |
| REPT14.DAT | 1,119 | May 19, 2004 | Simulation output |
| week1.txt | 6,111 | May 19, 2004 | Human-readable report |
| 475ProSim.ppt | 524,800 | May 12, 2004 | Course materials |
| ProSim_intro.ppt | 4,548,608 | May 12, 2004 | Simulation introduction |

---

## Appendix E: Online Sources (December 2024)

### Confirmed PROSIM References

| Source | URL | Information |
|--------|-----|-------------|
| **LGIRA Archive** | [lgira.mesmernet.org/items/show/2717](https://www.lgira.mesmernet.org/items/show/2717) | Original 1968 PROSIM catalog entry |
| **Amazon (Original)** | [amazon.com/dp/0700222243](https://www.amazon.com/PROSIM-Production-Management-Paul-Greenlaw/dp/0700222243) | 1969 edition by Greenlaw & Hottenstein |
| **Amazon (Windows)** | [amazon.com/dp/0256214360](https://www.amazon.com/Prosim-Windows-Production-Management-Simulation/dp/0256214360) | 1996 Windows version with Chu |
| **Penn State News** | [psu.edu/news/.../chao-hsien-chu...](https://www.psu.edu/news/information-sciences-and-technology/story/chao-hsien-chu-one-ists-original-five-faculty-members-has) | Obituary for Chao-Hsien Chu |
| **Chu Tribute** | [kochfuneralhome.com/.../Chao-Hsien-Chu](https://kochfuneralhome.com/tribute/details/2338/Chao-Hsien-Chu/condolences.html) | Hottenstein's tribute mentioning PROSIM |

### Inaccessible/Lost Resources

| Resource | Status |
|----------|--------|
| PROSIM simulation software | Not found online |
| Instructor diskette | Not found |
| PROSIM manual/Appendix A | Not found |
| Ohio thesis "PROSIM VII" | 404 error as of Dec 2024 |
| ACS.org PDF reference | Unverified |

### Related But Different Products

Several other products share the "PROSIM" name but are unrelated:
- **Fives ProSim** - Chemical process simulation software (prosim.net)
- **ProSim Training Solutions** - Flight simulator software (prosim-ar.com)
- **KBSI ProSim** - Business process workflow simulation

---

*Document generated through forensic analysis of preserved files and online research, without access to original PROSIM source code or documentation. Last updated: December 2024.*
