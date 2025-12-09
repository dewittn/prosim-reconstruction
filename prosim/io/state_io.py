"""
Game state persistence for PROSIM.

This module handles saving and loading game state to JSON files,
supporting multiple save slots and auto-save functionality.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from prosim.config.schema import ProsimConfig, get_default_config
from prosim.models.company import Company, GameState


class SaveMetadata(BaseModel):
    """Metadata for a saved game."""

    save_name: str = Field(description="Display name for this save")
    save_slot: int = Field(ge=0, description="Save slot number (0 = autosave)")
    game_id: str = Field(description="Game identifier")
    current_week: int = Field(ge=1, description="Current game week")
    company_name: str = Field(default="", description="Player's company name")
    total_costs: float = Field(default=0.0, description="Cumulative costs")
    created_at: str = Field(description="ISO timestamp when save was created")
    updated_at: str = Field(description="ISO timestamp when save was last updated")
    version: str = Field(default="0.1.0", description="PROSIM version")


class SavedGame(BaseModel):
    """Complete saved game including metadata and state."""

    metadata: SaveMetadata
    game_state: GameState
    config: Optional[ProsimConfig] = Field(
        default=None, description="Game configuration (uses defaults if None)"
    )


class SaveError(Exception):
    """Exception raised when saving fails."""

    pass


class LoadError(Exception):
    """Exception raised when loading fails."""

    pass


def get_default_saves_dir() -> Path:
    """Get the default directory for save files.

    Returns:
        Path to saves directory (creates if not exists)
    """
    # Use XDG Base Directory spec on Linux/macOS
    if os.name == "posix":
        xdg_data = os.environ.get("XDG_DATA_HOME", "")
        if xdg_data:
            saves_dir = Path(xdg_data) / "prosim" / "saves"
        else:
            saves_dir = Path.home() / ".local" / "share" / "prosim" / "saves"
    else:
        # Windows: use AppData
        app_data = os.environ.get("APPDATA", "")
        if app_data:
            saves_dir = Path(app_data) / "prosim" / "saves"
        else:
            saves_dir = Path.home() / ".prosim" / "saves"

    saves_dir.mkdir(parents=True, exist_ok=True)
    return saves_dir


def get_save_path(slot: int, saves_dir: Optional[Path] = None) -> Path:
    """Get the file path for a save slot.

    Args:
        slot: Save slot number (1-based)
        saves_dir: Directory for saves (uses default if None)

    Returns:
        Path to save file
    """
    if saves_dir is None:
        saves_dir = get_default_saves_dir()
    return saves_dir / f"save_{slot:02d}.json"


def get_autosave_path(saves_dir: Optional[Path] = None) -> Path:
    """Get the file path for auto-save.

    Args:
        saves_dir: Directory for saves (uses default if None)

    Returns:
        Path to auto-save file
    """
    if saves_dir is None:
        saves_dir = get_default_saves_dir()
    return saves_dir / "autosave.json"


def save_game(
    game_state: GameState,
    slot: int,
    save_name: Optional[str] = None,
    config: Optional[ProsimConfig] = None,
    saves_dir: Optional[Path] = None,
) -> Path:
    """Save game state to a slot.

    Args:
        game_state: Current game state to save
        slot: Save slot number (1-based)
        save_name: Display name for this save (auto-generated if None)
        config: Game configuration (saved with state)
        saves_dir: Directory for saves (uses default if None)

    Returns:
        Path to saved file

    Raises:
        SaveError: If saving fails
    """
    if slot < 1:
        raise SaveError("Save slot must be >= 1")

    # Get company info for metadata
    company = game_state.get_company(1)
    company_name = company.name if company else ""
    total_costs = company.total_costs if company else 0.0

    now = datetime.now().isoformat()

    # Check if this is an update to existing save
    save_path = get_save_path(slot, saves_dir)
    created_at = now
    if save_path.exists():
        try:
            existing = load_game(slot, saves_dir)
            created_at = existing.metadata.created_at
        except LoadError:
            pass

    # Generate save name if not provided
    if save_name is None:
        save_name = f"Week {game_state.current_week}"
        if company_name:
            save_name = f"{company_name} - {save_name}"

    metadata = SaveMetadata(
        save_name=save_name,
        save_slot=slot,
        game_id=game_state.game_id,
        current_week=game_state.current_week,
        company_name=company_name,
        total_costs=total_costs,
        created_at=created_at,
        updated_at=now,
    )

    saved_game = SavedGame(
        metadata=metadata,
        game_state=game_state,
        config=config,
    )

    try:
        # Ensure directory exists
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Write atomically by writing to temp file first
        temp_path = save_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(saved_game.model_dump_json(indent=2))

        # Replace old file with new one
        temp_path.replace(save_path)

        return save_path

    except OSError as e:
        raise SaveError(f"Failed to save game: {e}") from e


def load_game(
    slot: int,
    saves_dir: Optional[Path] = None,
) -> SavedGame:
    """Load game state from a slot.

    Args:
        slot: Save slot number (1-based)
        saves_dir: Directory for saves (uses default if None)

    Returns:
        SavedGame with metadata and state

    Raises:
        LoadError: If loading fails
    """
    save_path = get_save_path(slot, saves_dir)

    if not save_path.exists():
        raise LoadError(f"No save found in slot {slot}")

    try:
        with open(save_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return SavedGame.model_validate(data)

    except json.JSONDecodeError as e:
        raise LoadError(f"Corrupt save file in slot {slot}: {e}") from e
    except Exception as e:
        raise LoadError(f"Failed to load game from slot {slot}: {e}") from e


def load_game_from_path(path: Path) -> SavedGame:
    """Load game state from a specific file path.

    Args:
        path: Path to save file

    Returns:
        SavedGame with metadata and state

    Raises:
        LoadError: If loading fails
    """
    if not path.exists():
        raise LoadError(f"Save file not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return SavedGame.model_validate(data)

    except json.JSONDecodeError as e:
        raise LoadError(f"Corrupt save file: {e}") from e
    except Exception as e:
        raise LoadError(f"Failed to load game: {e}") from e


def autosave(
    game_state: GameState,
    config: Optional[ProsimConfig] = None,
    saves_dir: Optional[Path] = None,
) -> Path:
    """Auto-save game state.

    This saves to a dedicated autosave file, separate from manual saves.

    Args:
        game_state: Current game state to save
        config: Game configuration
        saves_dir: Directory for saves (uses default if None)

    Returns:
        Path to saved file

    Raises:
        SaveError: If saving fails
    """
    company = game_state.get_company(1)
    company_name = company.name if company else ""
    total_costs = company.total_costs if company else 0.0

    now = datetime.now().isoformat()

    # Check if this is an update
    autosave_path = get_autosave_path(saves_dir)
    created_at = now
    if autosave_path.exists():
        try:
            existing = load_autosave(saves_dir)
            # Only preserve created_at if same game
            if existing.metadata.game_id == game_state.game_id:
                created_at = existing.metadata.created_at
        except LoadError:
            pass

    metadata = SaveMetadata(
        save_name=f"Autosave - Week {game_state.current_week}",
        save_slot=0,  # 0 indicates autosave
        game_id=game_state.game_id,
        current_week=game_state.current_week,
        company_name=company_name,
        total_costs=total_costs,
        created_at=created_at,
        updated_at=now,
    )

    saved_game = SavedGame(
        metadata=metadata,
        game_state=game_state,
        config=config,
    )

    try:
        autosave_path.parent.mkdir(parents=True, exist_ok=True)

        temp_path = autosave_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(saved_game.model_dump_json(indent=2))

        temp_path.replace(autosave_path)
        return autosave_path

    except OSError as e:
        raise SaveError(f"Failed to autosave: {e}") from e


def load_autosave(saves_dir: Optional[Path] = None) -> SavedGame:
    """Load autosaved game state.

    Args:
        saves_dir: Directory for saves (uses default if None)

    Returns:
        SavedGame with metadata and state

    Raises:
        LoadError: If loading fails or no autosave exists
    """
    autosave_path = get_autosave_path(saves_dir)

    if not autosave_path.exists():
        raise LoadError("No autosave found")

    try:
        with open(autosave_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return SavedGame.model_validate(data)

    except json.JSONDecodeError as e:
        raise LoadError(f"Corrupt autosave file: {e}") from e
    except Exception as e:
        raise LoadError(f"Failed to load autosave: {e}") from e


def delete_save(slot: int, saves_dir: Optional[Path] = None) -> bool:
    """Delete a save slot.

    Args:
        slot: Save slot number (1-based)
        saves_dir: Directory for saves (uses default if None)

    Returns:
        True if deleted, False if didn't exist
    """
    save_path = get_save_path(slot, saves_dir)
    if save_path.exists():
        save_path.unlink()
        return True
    return False


def delete_autosave(saves_dir: Optional[Path] = None) -> bool:
    """Delete the autosave file.

    Args:
        saves_dir: Directory for saves (uses default if None)

    Returns:
        True if deleted, False if didn't exist
    """
    autosave_path = get_autosave_path(saves_dir)
    if autosave_path.exists():
        autosave_path.unlink()
        return True
    return False


def list_saves(saves_dir: Optional[Path] = None) -> list[SaveMetadata]:
    """List all available save files.

    Args:
        saves_dir: Directory for saves (uses default if None)

    Returns:
        List of SaveMetadata for each valid save file
    """
    if saves_dir is None:
        saves_dir = get_default_saves_dir()

    saves = []

    # Check autosave
    autosave_path = get_autosave_path(saves_dir)
    if autosave_path.exists():
        try:
            saved = load_autosave(saves_dir)
            saves.append(saved.metadata)
        except LoadError:
            pass

    # Check numbered slots
    for save_file in saves_dir.glob("save_*.json"):
        try:
            # Extract slot number from filename
            slot_str = save_file.stem.replace("save_", "")
            slot = int(slot_str)
            saved = load_game(slot, saves_dir)
            saves.append(saved.metadata)
        except (ValueError, LoadError):
            pass

    # Sort by updated_at (most recent first)
    saves.sort(key=lambda m: m.updated_at, reverse=True)
    return saves


def has_autosave(saves_dir: Optional[Path] = None) -> bool:
    """Check if an autosave exists.

    Args:
        saves_dir: Directory for saves (uses default if None)

    Returns:
        True if autosave exists
    """
    return get_autosave_path(saves_dir).exists()


def get_save_info(slot: int, saves_dir: Optional[Path] = None) -> Optional[SaveMetadata]:
    """Get metadata for a save slot without loading full state.

    Args:
        slot: Save slot number (1-based)
        saves_dir: Directory for saves (uses default if None)

    Returns:
        SaveMetadata if save exists, None otherwise
    """
    try:
        saved = load_game(slot, saves_dir)
        return saved.metadata
    except LoadError:
        return None


def export_save(
    slot: int,
    output_path: Path,
    saves_dir: Optional[Path] = None,
) -> None:
    """Export a save file to a different location.

    Args:
        slot: Save slot number (1-based)
        output_path: Destination path
        saves_dir: Directory for saves (uses default if None)

    Raises:
        LoadError: If save doesn't exist
        SaveError: If export fails
    """
    save_path = get_save_path(slot, saves_dir)
    if not save_path.exists():
        raise LoadError(f"No save found in slot {slot}")

    try:
        import shutil

        shutil.copy2(save_path, output_path)
    except OSError as e:
        raise SaveError(f"Failed to export save: {e}") from e


def import_save(
    input_path: Path,
    slot: int,
    saves_dir: Optional[Path] = None,
) -> SaveMetadata:
    """Import a save file from another location.

    Args:
        input_path: Source save file path
        slot: Target save slot number
        saves_dir: Directory for saves (uses default if None)

    Returns:
        Metadata of imported save

    Raises:
        LoadError: If import file is invalid
        SaveError: If import fails
    """
    # Validate the file first
    try:
        saved = load_game_from_path(input_path)
    except LoadError as e:
        raise LoadError(f"Invalid save file: {e}") from e

    # Update slot number in metadata
    saved.metadata.save_slot = slot
    saved.metadata.updated_at = datetime.now().isoformat()

    # Save to target slot
    save_path = get_save_path(slot, saves_dir)
    try:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(saved.model_dump_json(indent=2))
        return saved.metadata
    except OSError as e:
        raise SaveError(f"Failed to import save: {e}") from e
