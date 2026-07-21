# CLAUDE.md - PROSIM Reconstruction Project

## Hard Rules

- **Always use Docker** for the web interface: `docker compose --profile dev up prosim-dev`
- **Always use `playwright-cli` via Bash** (`/Users/dewittn/.bun/bin/playwright-cli`), never Playwright MCP tools
- **App URL**: `https://prosim-dev.prosim-reconstruction.orb.local`
- **Never modify verified mechanics** without explicit user request — check `docs/forensic_verification_status.md` first
- **Record key discoveries** in `docs/key_discoveries.md` using the template there

## Project Overview

Reconstruction of **PROSIM III for Windows** (1996, Chu/Hottenstein/Greenlaw, Irwin/McGraw-Hill). The original software is lost; we're rebuilding from forensic analysis of archived game files from a 2004 college course. Goal: identical results given the same inputs. Two separate "PROSIM" lineages exist — ours is the Greenlaw commercial product, NOT the Mize academic one (see `docs/history.md`).

## Commands

```bash
# Run tests (local, not Docker)
.venv/bin/pytest

# Run CLI
.venv/bin/python -m prosim.cli.main
```

### Docker Development (primary)

```bash
# Pre-flight: ensure OrbStack context
docker context show          # Should be "orbstack"

# Day-to-day startup
docker compose --profile dev up prosim-dev

# First run or after changing pyproject.toml
docker compose --profile dev up prosim-dev --build

# Stop
docker compose --profile dev down
```

Source is bind-mounted — static/template changes are instant, Python changes auto-restart via uvicorn `--reload`. Only `pyproject.toml` changes need `--build`.

## Verification Gates

Before modifying simulation mechanics, check `docs/forensic_verification_status.md`:

- **VERIFIED** — Do not change without explicit request
- **PARTIAL** — Changes OK, document reasoning
- **UNKNOWN** — Make configurable, flag uncertainty

## Key Principles

1. **Historical Accuracy**: Match original behavior exactly where possible
2. **Document Everything**: All discoveries go in IMPLEMENTATION_PLAN.md
3. **Verify Against Archive**: Use original files to validate formulas
4. **Authentic Output**: Reports should match what students saw in 2004

## Key Files

| File                                   | Purpose                                               |
| -------------------------------------- | ----------------------------------------------------- |
| `docs/forensic_verification_status.md` | **START HERE** — Verification status of all mechanics |
| `docs/key_discoveries.md`              | Chronicle of major forensic discoveries with evidence |
| `IMPLEMENTATION_PLAN.md`               | Detailed roadmap and progress log                     |
| `docs/algorithms.md`                   | Technical documentation of all algorithms             |
| `prosim/config/defaults.py`            | All game constants with verification notes            |
| `prosim/io/rept_parser.py`             | REPT file parsing and human-readable output           |

## Reference Docs

| Doc                              | Content                                                     |
| -------------------------------- | ----------------------------------------------------------- |
| `docs/history.md`                | Product lineage, background story, 2004 reverse-engineering |
| `docs/archive-guide.md`          | Archive structure, Nelson.xls, original data location       |
| `docs/verification_guide.md`     | How to verify mechanics against original files              |
| `docs/xtc_verification_guide.md` | XTC binary file analysis and open hypotheses                |
