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
from prosim.io.state_io import (
    LoadError,
    SavedGame,
    SaveError,
    SaveMetadata,
    autosave,
    delete_autosave,
    delete_save,
    export_save,
    get_autosave_path,
    get_default_saves_dir,
    get_save_info,
    get_save_path,
    has_autosave,
    import_save,
    list_saves,
    load_autosave,
    load_game,
    load_game_from_path,
    save_game,
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
    # State I/O
    "SaveError",
    "LoadError",
    "SaveMetadata",
    "SavedGame",
    "save_game",
    "load_game",
    "load_game_from_path",
    "autosave",
    "load_autosave",
    "delete_save",
    "delete_autosave",
    "list_saves",
    "has_autosave",
    "get_save_info",
    "get_save_path",
    "get_autosave_path",
    "get_default_saves_dir",
    "export_save",
    "import_save",
]
