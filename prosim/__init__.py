"""
PROSIM - A Production Management Simulation

A reconstruction of the PROSIM simulation game originally created in 1968
by Paul S. Greenlaw and Michael P. Hottenstein.

This package provides:
- Core simulation engine for production management
- File I/O for DECS (decisions) and REPT (reports) formats
- CLI interface for playing the game
- Configurable parameters for simulation tuning

For historical context, see the docs/history.md file.
"""

__version__ = "0.1.0"
__author__ = "Nelson DeWitt"
__original_authors__ = [
    "Paul S. Greenlaw",
    "Michael P. Hottenstein",
    "Chao-Hsien Chu",
]

from prosim.config.defaults import DEFAULT_CONFIG

__all__ = [
    "__version__",
    "DEFAULT_CONFIG",
]
