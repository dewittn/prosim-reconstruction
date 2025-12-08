# PROSIM Reconstruction

A modern open-source reconstruction of **PROSIM**, a production management simulation game originally created in 1968 by Paul S. Greenlaw and Michael P. Hottenstein.

## About

PROSIM was one of the earliest computer-based business simulation games, originally written in FORTRAN for IBM mainframes and later updated for Windows in 1996. The simulation teaches production management concepts including:

- Inventory management (raw materials, parts, finished goods)
- Workforce scheduling and training
- Production planning across multiple departments
- Cost control and budgeting
- Demand forecasting

The original software is now abandonware with no known copies available online. This project reconstructs the simulation based on reverse-engineered spreadsheets and preserved course materials from a 2004 college course.

## Project Status

🚧 **Under Development** - See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for roadmap.

## Historical Context

- **1968**: Original PROSIM created by Greenlaw & Hottenstein (IBM mainframe, FORTRAN)
- **1996**: PROSIM III for Windows released (Chu, Hottenstein, Greenlaw)
- **2004**: Course materials and reverse-engineered spreadsheets preserved
- **2024**: This reconstruction project initiated

For detailed historical analysis, see [archive/docs/PROSIM_CASE_STUDY.md](archive/docs/PROSIM_CASE_STUDY.md).

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

*Coming soon - CLI and web interface in development*

```bash
# Start a new game (planned)
prosim new

# Load existing game (planned)
prosim load saves/my_game.json

# Process a DECS file (planned)
prosim process --decs input.DAT --state state.json
```

## Documentation

- [Implementation Plan](IMPLEMENTATION_PLAN.md) - Development roadmap and task tracking
- [Game Manual](docs/game_manual.md) - How to play *(coming soon)*
- [Algorithms](docs/algorithms.md) - Technical documentation *(coming soon)*
- [Case Study](archive/docs/PROSIM_CASE_STUDY.md) - Historical analysis

## Contributing

Contributions are welcome! This project has a preservation mission, so we especially appreciate:

- **Translations** - Help make the game accessible in more languages
- **Historical information** - Additional documentation about the original PROSIM
- **Testing** - Validation against any original PROSIM materials you may have

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines *(coming soon)*.

## Acknowledgments

### Original Authors
- **Paul S. Greenlaw** - Original co-author (1968)
- **Michael P. Hottenstein** - Original co-author (1968)
- **Chao-Hsien Chu** (1951-2021) - Co-author of Windows version (1996)

### Reconstruction
- **Nelson DeWitt** - Reverse engineering (2004), reconstruction (2024)

### Preservation Resources
- [Learning Games Initiative Research Archive (LGIRA)](https://www.lgira.mesmernet.org/items/show/2717)

## License

MIT License - See [LICENSE](LICENSE) for details.

This is a clean-room reconstruction based on observed behavior of the original software, not a copy or derivative of the original source code.

---

*"Those who cannot remember the past are condemned to repeat it."* - But in this case, we're trying to make sure you **can** repeat it, for educational purposes.
