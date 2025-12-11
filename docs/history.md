# PROSIM: A History of Preservation

> Preserving 55+ years of educational software history

## The Story of PROSIM

PROSIM (Production Simulation) is one of the pioneering educational simulation games in the field of operations management. This document tells the story of its origins, evolution, and eventual reconstruction.

---

## Origins (1968)

### The Birth of Business Simulations

In the late 1950s and 1960s, computer-based business simulations emerged as a new educational tool. The first business simulation game was created by the American Management Association in 1956, followed by computer-based versions developed by McKinsey & Company in 1957.

By 1968, universities were increasingly interested in simulation-based teaching methods for business courses. It was in this environment that **PROSIM** was created.

### The Original Authors

**Paul S. Greenlaw** and **Michael P. Hottenstein** created PROSIM in 1968 at Penn State University. The simulation was designed to teach production and operations management concepts through hands-on decision-making.

| Author | Contribution |
|--------|--------------|
| **Paul S. Greenlaw** | Original co-author (1968), continued involvement through Windows versions |
| **Michael P. Hottenstein** | Original co-author (1968), Penn State faculty member |

The simulation was originally written in FORTRAN for IBM 700/7000 series mainframes, one of the dominant computing platforms of the era.

### Original Design Philosophy

From the [Learning Games Initiative Research Archive (LGIRA)](https://www.lgira.mesmernet.org/items/show/2717):

> "Players manage the production operations of a firm by making periodic decisions across quality control, plant maintenance, job scheduling, workforce management, and inventory management."

The original PROSIM was designed as a companion to instructional texts, allowing students to apply theoretical concepts in a realistic simulated environment.

---

## Evolution (1969-1996)

### Publication History

| Year | Version | Publisher | Platform |
|------|---------|-----------|----------|
| 1968 | PROSIM (Original) | - | IBM Mainframe (FORTRAN) |
| 1969 | PROSIM | International Textbook Co. | IBM Mainframe |
| 1970s-80s | PROSIM II | Various | Updated mainframes |
| 1996 | PROSIM III for Windows | Irwin Professional Pub | Windows 3.1/95 |

### The Windows Era

By the mid-1990s, personal computers had become ubiquitous in education. The simulation was updated for Windows, with **Chao-Hsien Chu** joining as the third author.

**Chao-Hsien Chu** (1951-2021) was a native of Qiaotou, Taiwan, who earned his PhD from Penn State's Smeal College of Business in 1984. He was one of Hottenstein's graduate students and, as Hottenstein later wrote in a tribute: *"After he graduated we collaborated on the development of PROSIM, a computer based simulation. His computer skills were first rate."*

Chu later became one of the original five faculty members of Penn State's College of Information Sciences and Technology in 1999.

### Widespread Adoption

PROSIM was used in operations management courses at universities including:
- Penn State University
- Bryant University (formerly Bryant College)
- Various other business schools

The simulation taught generations of students about:
- Material Requirements Planning (MRP)
- Inventory management
- Workforce planning
- Cost-benefit analysis
- Demand forecasting

---

## The Lost Software Problem

### Why PROSIM Disappeared

Despite nearly four decades of use, PROSIM effectively disappeared within a few years of the final Windows version. Several factors contributed:

1. **Proprietary Distribution**: The simulation was bundled with textbooks and required an "instructor diskette" to run - it was never sold as standalone software.

2. **Platform Lock-in**: The Windows 3.1/95 version was never updated for modern operating systems.

3. **Physical Media Dependency**: Distribution via 3.5" floppy disks meant copies degraded and became inaccessible as floppy drives disappeared.

4. **Publisher Changes**: Irwin was acquired by McGraw-Hill, and the product line was discontinued.

5. **No Source Release**: The algorithms and source code were never published or open-sourced.

6. **Author Retirements/Deaths**: As the original authors retired or passed away (Dr. Chu in 2021), institutional knowledge was lost.

### What Survives

As of 2025, no copies of the PROSIM simulation software are known to exist online:
- The simulation executable is not archived
- The instructor diskette (required to run) is unavailable
- No source code was ever published
- The PROSIM manual is not preserved
- An Ohio University thesis "PROSIM VII: An Enhanced Production Simulation" is inaccessible

The only remaining documentation exists in:
1. The [LGIRA archive entry](https://www.lgira.mesmernet.org/items/show/2717) describing the original 1968 version
2. Amazon listings for out-of-print books
3. Scattered course materials
4. **The reverse-engineered spreadsheet from 2004**

---

## The Reconstruction Project

### The 2004 Spreadsheet

In Summer 2004, a student in Bryant College's MGMT 475 course (Managing the Production Process) reverse-engineered PROSIM. Unable to see the simulation's internal algorithms, they systematically:

1. Tracked all inputs and outputs across multiple simulation weeks
2. Identified patterns in production rates, costs, and efficiency
3. Built a predictive Excel spreadsheet
4. Achieved approximately **97% accuracy** in predicting simulation outcomes

This spreadsheet, **ProsimTable.xls**, became one of the most detailed surviving records of how PROSIM actually functioned.

### Why Reconstruct PROSIM?

**Educational Value**: PROSIM taught fundamental operations management concepts that remain relevant today. A modern reconstruction makes this educational tool accessible to new generations.

**Historical Preservation**: As one of the earliest computer-based business simulations (1968), PROSIM represents an important milestone in the history of educational technology.

**Open Access**: The original simulation was proprietary and required instructor involvement. An open-source reconstruction allows self-paced learning.

**Technical Challenge**: Reconstructing a simulation from limited evidence (output files, spreadsheets, course materials) is an interesting reverse-engineering challenge.

### Reconstruction Approach

This project uses a **clean-room reconstruction** methodology:

1. **No Original Code**: The reconstruction is based purely on observed behavior, not any original source code (which was never available).

2. **Evidence-Based**: All game mechanics are derived from preserved DECS/REPT files, the reverse-engineered spreadsheet, and course materials.

3. **Documented Uncertainty**: Parameters that couldn't be definitively determined are clearly marked as "estimated" and made configurable.

4. **Modern Technology**: The reconstruction uses modern Python with type hints, Pydantic models, and comprehensive testing.

---

## Honoring the Original Authors

### Paul S. Greenlaw

Original co-author of PROSIM in 1968. Continued involvement through subsequent versions. His work in educational simulation contributed to the field of experiential learning in business education.

### Michael P. Hottenstein

Original co-author of PROSIM in 1968. Penn State faculty member who continued as author through PROSIM III. Maintained the simulation through multiple decades and platform transitions.

### Chao-Hsien Chu (1951-2021)

Added as co-author for the Windows version. Born in Qiaotou, Taiwan, he earned his PhD from Penn State's Smeal College of Business in 1984. He became one of the founding faculty members of Penn State's College of Information Sciences and Technology.

Dr. Chu passed away on January 15, 2021. His contributions to PROSIM and information sciences education are remembered by colleagues and students.

---

## Archive Resources

### Learning Games Initiative Research Archive (LGIRA)

The [LGIRA](https://www.lgira.mesmernet.org/) maintains a catalog entry for the original 1968 PROSIM:

**URL**: [https://www.lgira.mesmernet.org/items/show/2717](https://www.lgira.mesmernet.org/items/show/2717)

This entry documents the original publication, platform (IBM mainframes), and authors.

### Original Publications

| Title | Year | ISBN | Status |
|-------|------|------|--------|
| PROSIM: A Production Management Simulation | 1969 | 978-0700222247 | Out of print |
| PROSIM III for Windows | 1996 | 978-0256214352 | Out of print |

Amazon listings exist but no sellers typically have copies available.

### Preserved Materials in This Project

The `archive/` directory contains preserved materials from actual PROSIM gameplay:

```
archive/
├── data/
│   ├── DECS12.txt      # Decision file (week 12)
│   ├── DECS14.txt      # Decision file (week 14)
│   ├── REPT12.DAT      # Report file (week 12)
│   ├── REPT13.DAT      # Report file (week 13)
│   ├── REPT14.DAT      # Report file (week 14)
│   └── week1.txt       # Human-readable report (Rosetta Stone)
├── docs/
│   ├── PROSIM_CASE_STUDY.md  # Forensic analysis
│   ├── 475ProSim.ppt   # Course introduction
│   └── ProSim_intro.ppt # Simulation mechanics
└── spreadsheets/
    ├── ProsimTable.xls # Reverse-engineered model
    └── Prosim Template.xls # Planning template
```

---

## Contributing to Preservation

### Help Us Find More PROSIM Data

**Did you play PROSIM in college?** We're seeking:

- **DECS/REPT Files**: Any decision or report files from gameplay
- **Original Textbook**: "PROSIM: A Production Management Simulation"
- **Documentation**: Manuals, instructor guides, or course materials
- **Screenshots**: Images of the original software
- **Memories**: Descriptions of how the game worked

Even a single DECS/REPT pair would be valuable for validation.

### Contact

If you have any PROSIM materials or information:
- Open an issue on the [GitHub repository](https://github.com/yourusername/prosim-reconstruction)
- The LGIRA may also be interested in supplementary materials

### Preservation Partners

Consider contributing to:
- [Internet Archive](https://archive.org) - General software preservation
- [Learning Games Initiative Research Archive](https://www.lgira.mesmernet.org/) - Educational game history
- [Computer History Museum](https://computerhistory.org) - Computing history

---

## Timeline

| Year | Event |
|------|-------|
| 1956 | First business simulation game (AMA) |
| 1957 | First computer-based business game (McKinsey) |
| 1968 | **PROSIM created** by Greenlaw & Hottenstein |
| 1969 | First published textbook version |
| 1970s-80s | PROSIM II widely used in business schools |
| 1996 | PROSIM III for Windows released |
| 2004 | Reverse-engineered spreadsheet created |
| 2021 | Dr. Chao-Hsien Chu passes away |
| 2025 | This reconstruction project initiated |

---

## Acknowledgments

This reconstruction project acknowledges:

- **Paul S. Greenlaw**, **Michael P. Hottenstein**, and **Chao-Hsien Chu** for creating and maintaining PROSIM
- The LGIRA for preserving information about the original simulation
- Bryant University (formerly Bryant College) where the reverse-engineering was performed
- All the students and instructors who used PROSIM over nearly four decades

---

*"Those who cannot remember the past are condemned to repeat it." - George Santayana*

*But in this case, we're trying to make sure you CAN repeat it - for educational purposes.*

---

*This documentation is part of the PROSIM Reconstruction Project. For the complete forensic analysis, see [PROSIM_CASE_STUDY.md](../archive/docs/PROSIM_CASE_STUDY.md).*
