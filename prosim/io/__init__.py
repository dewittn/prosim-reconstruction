"""
File I/O for PROSIM.

This module handles reading and writing of:
- DECS files (decision input)
- REPT files (report output)
- Game state persistence (JSON)
"""

from prosim.io.decs_parser import (
    DECSParseError,
    DECSParser,
    parse_decs,
    write_decs,
)

__all__ = [
    "DECSParseError",
    "DECSParser",
    "parse_decs",
    "write_decs",
]

# I/O components will be imported here as they are implemented
# from prosim.io.rept_writer import write_rept, REPTWriter
# from prosim.io.state_io import save_state, load_state
