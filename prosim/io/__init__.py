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
from prosim.io.rept_parser import (
    REPTParseError,
    REPTParser,
    parse_rept,
    write_rept,
    write_rept_human_readable,
)

__all__ = [
    # DECS
    "DECSParseError",
    "DECSParser",
    "parse_decs",
    "write_decs",
    # REPT
    "REPTParseError",
    "REPTParser",
    "parse_rept",
    "write_rept",
    "write_rept_human_readable",
]

# I/O components will be imported here as they are implemented
# from prosim.io.state_io import save_state, load_state
