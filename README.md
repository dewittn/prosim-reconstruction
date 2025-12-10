# PROSIM - Production Management Simulation

> **A modern open-source reconstruction of the classic PROSIM business simulation game (1968-1996)**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: In Development](https://img.shields.io/badge/Status-In%20Development-orange)]()

## What is PROSIM?

**PROSIM** (Production Simulation) is a computer-based business simulation game that teaches production and operations management. Originally developed in **1968** by **Paul S. Greenlaw** and **Michael P. Hottenstein** at Penn State University, it was one of the pioneering educational simulations of its era.

The simulation was later updated and published as **"PROSIM: A Production Management Simulation"** with **Chao-Hsien Chu** joining as co-author for the Windows version (1996). The accompanying textbook was published by Prentice Hall.

### The Original Software

- **PROSIM (1968)** - IBM mainframe version written in FORTRAN
- **PROSIM II** - Updated mainframe version
- **PROSIM III for Windows (1996)** - Final commercial release by Chu, Hottenstein, and Greenlaw

The simulation was used in Operations Management courses at universities including Penn State, Bryant University, and others throughout the 1970s-2000s. Players manage a manufacturing company producing three products (X, Y, Z), making weekly decisions about:

- **Production scheduling** - Assigning operators to machines
- **Inventory management** - Ordering raw materials and parts
- **Workforce planning** - Hiring, training, and scheduling workers
- **Budget allocation** - Quality control, maintenance, and other overhead
- **Demand forecasting** - Predicting customer orders

### Why This Reconstruction?

The original PROSIM software is now **abandonware** - no copies are known to exist online, and the original authors have either retired or passed away (Dr. Chu passed in 2021). This project aims to:

1. **Preserve** the educational value of this classic simulation
2. **Reconstruct** the game mechanics through forensic analysis
3. **Modernize** the interface while maintaining authenticity
4. **Open-source** the simulation for future educational use

## Project Status

🚧 **Under Development** - See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for roadmap.

This reconstruction is based on:

- Reverse-engineered spreadsheets achieving ~97% prediction accuracy
- Preserved DECS (decision) and REPT (report) files from actual gameplay
- Course materials, presentations, and textbook references
- Forensic analysis of game mechanics through input/output correlation

## Historical Timeline

| Year          | Event                                                                             |
| ------------- | --------------------------------------------------------------------------------- |
| **1968**      | Original PROSIM created by Greenlaw & Hottenstein (Penn State, IBM FORTRAN)       |
| **1970s-80s** | PROSIM II developed and widely used in business schools                           |
| **1996**      | PROSIM III for Windows released (Chu, Hottenstein, Greenlaw)                      |
| **1996**      | _"PROSIM: A Production Management Simulation"_ textbook published (Prentice Hall) |
| **2000s**     | Still in use at various universities                                              |
| **2021**      | Dr. Chao-Hsien Chu passes away                                                    |
| **2025**      | This reconstruction project initiated                                             |

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/prosim-reconstruction.git
cd prosim-reconstruction

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -e .
```

## Usage

```bash
# Start a new game
prosim new --name "My Company"

# Start with specific random seed (for reproducibility)
prosim new --name "My Company" --seed 42

# Load a saved game
prosim load 1              # Load from slot 1
prosim load --autosave     # Load from autosave

# List saved games
prosim saves

# Process a DECS file (batch mode)
prosim process --decs input.DAT --slot 1

# Show information about PROSIM
prosim info

# Play in Spanish
prosim --lang es new --name "Mi Empresa"
```

## Documentation

- [Game Manual](docs/game_manual.md) - How to play, strategy guide, CLI reference
- [Technical Documentation](docs/algorithms.md) - Algorithms, API reference, configuration
- [Calibration Report](docs/calibration_report.md) - Parameter verification and accuracy analysis
- [History & Preservation](docs/history.md) - The story of PROSIM and this reconstruction
- [Case Study](archive/docs/PROSIM_CASE_STUDY.md) - Forensic analysis and reverse engineering
- [Implementation Plan](IMPLEMENTATION_PLAN.md) - Development roadmap and progress
- [Contributing](CONTRIBUTING.md) - How to contribute to the project

## 📢 Seeking PROSIM Data Files

**Did you play PROSIM in college?** We're looking for DECS (decision) and REPT (report) files from anyone who used PROSIM in courses or training programs. These files help us verify the accuracy of our reconstructed simulation.

**What we're looking for:**

- `DECS*.DAT` files (decision inputs)
- `REPT*.DAT` files (simulation reports)
- **State/save files** - We've **successfully decoded the `.XTC` file format** as PROSIM game state files! These contain hidden operator statistics (efficiency, proficiency) and weekly snapshots. If you have any `*.XTC` files, they would be extremely valuable for calibration!
- The original textbook: _"PROSIM: A Production Management Simulation"_
- Any documentation, manuals, or course materials
- Screenshots or printouts from the original software
- Memories of how the game worked!

**Important note about file usefulness:**

PROSIM is path-dependent - each week's output depends on all previous decisions. A REPT file from Week 12 reflects 11 weeks of prior choices (training, inventory, hiring, etc.). This means:

- **Most valuable:** Complete game sequences (DECS1→REPT1, DECS2→REPT2, ... through week 24) from a single playthrough
- **Very useful:** Week 1 REPT files (show initial state before player decisions)
- **Still helpful:** Partial sequences, even just 2-3 consecutive weeks
- **Limited use:** Isolated late-game files without preceding weeks

If you have any of these from the 1970s-2000s era, please [open an issue](https://github.com/yourusername/prosim-reconstruction/issues) or contact us.

### Keywords for Fellow Searchers

If you found this page searching for any of these terms, you're in the right place:

> PROSIM simulation, PROSIM III, PROSIM for Windows, Greenlaw Hottenstein simulation,
> Chao-Hsien Chu PROSIM, Penn State production simulation, production management simulation game,
> PROSIM Prentice Hall, PROSIM business simulation, PROSIM operations management,
> DECS DAT file, REPT DAT file, PROSIM course, Bryant University PROSIM

## Contributing

Contributions are welcome! This project has a preservation mission, so we especially appreciate:

- **DECS/REPT Files** - Help validate our simulation accuracy (see above)
- **Historical Information** - Documentation about the original PROSIM
- **Translations** - Help make the game accessible in more languages
- **Testing** - Validation against any original PROSIM materials you may have
- **Code Contributions** - Help build the reconstruction

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Technical Details

### Simulation Mechanics (Discovered Through Forensic Analysis)

The reconstruction is based on detailed analysis of preserved game files. Key findings include:

- **Production rates**: Parts (60/50/40 per hour), Assembly (40/30/20 per hour)
- **Quality budget impact**: Higher quality budget reduces reject rate (~10-18%)
- **Operator training**: Workers improve efficiency over 3-4 weeks of continuous work
- **Demand forecasting**: Uses EWMA (Exponentially Weighted Moving Average)
- **Cost structures**: Labor ($10/hr), overtime (1.5x), various overhead categories

For complete technical details, see the [Case Study](archive/docs/PROSIM_CASE_STUDY.md).

### File Formats

- **DECS files**: Weekly decision inputs (operator assignments, orders, budgets)
- **REPT files**: Simulation output reports (costs, production, inventory, performance)
- **XTC files**: Game state save files containing:
  - Hidden operator attributes (base efficiency 64-103%, proficiency 55-68%)
  - Weekly state snapshots appended as game progresses
  - Workforce tracking (operator count stored in header byte 9)
  - Evidence of "expert" operators who exceed 100% efficiency

## Acknowledgments

### Original Authors

- **Paul S. Greenlaw** - Original co-author (1968), Penn State University
- **Michael P. Hottenstein** - Original co-author (1968), Penn State University
- **Chao-Hsien Chu** (1951-2021) - Co-author of Windows version (1996), Penn State University

### Reconstruction

- **Nelson DeWitt** - Reverse engineering (2004), reconstruction (2025)

### Preservation Resources

- [Learning Games Initiative Research Archive (LGIRA)](https://www.lgira.mesmernet.org/items/show/2717) - Archive entry for PROSIM

## Related Projects & Resources

- [LGIRA](https://www.lgira.mesmernet.org/) - Learning Games Initiative Research Archive
- [Computer Simulation Archive](https://www.simulationarchive.org/) - General simulation preservation

**Note:** There are several unrelated products that share the "PROSIM" name:

- Fives ProSim (prosim.net) - Chemical process simulation
- ProSim Aviation (prosim-ar.com) - Flight simulator software
- KBSI ProSim - Business process workflow simulation

This project reconstructs the _educational production management simulation_, not any of the above.

## License

MIT License - See [LICENSE](LICENSE) for details.

This is a **clean-room reconstruction** based on observed behavior of the original software, not a copy or derivative of the original source code.

---

<p align="center">
<i>"Those who cannot remember the past are condemned to repeat it."</i><br>
But in this case, we're trying to make sure you <b>can</b> repeat it — for educational purposes.
</p>

<p align="center">
<b>Help preserve educational software history!</b><br>
⭐ Star this repo | 🔀 Fork and contribute | 📢 Share with former classmates
</p>
