"""Tests for game state persistence."""

import json
import tempfile
from pathlib import Path

import pytest

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
    get_save_path,
    has_autosave,
    import_save,
    list_saves,
    load_autosave,
    load_game,
    load_game_from_path,
    save_game,
)
from prosim.models.company import Company, GameState


@pytest.fixture
def temp_saves_dir():
    """Create a temporary directory for test saves."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_game_state():
    """Create a sample game state for testing."""
    return GameState.create_single_player(
        game_id="test-game-001",
        company_name="Test Company",
        max_weeks=15,
        random_seed=42,
    )


@pytest.fixture
def sample_game_state_advanced():
    """Create a more advanced game state (simulating progress)."""
    state = GameState.create_single_player(
        game_id="test-game-002",
        company_name="Advanced Corp",
        max_weeks=15,
        random_seed=123,
    )
    # Simulate some progress
    company = state.get_company(1)
    company = company.model_copy(
        update={
            "current_week": 5,
            "total_costs": 15000.0,
        }
    )
    state = state.update_company(company)
    state = state.model_copy(update={"current_week": 5})
    return state


class TestSaveMetadata:
    """Tests for SaveMetadata model."""

    def test_create_metadata(self):
        """Test creating save metadata."""
        metadata = SaveMetadata(
            save_name="Test Save",
            save_slot=1,
            game_id="test-001",
            current_week=3,
            company_name="My Company",
            total_costs=5000.0,
            created_at="2024-12-09T10:00:00",
            updated_at="2024-12-09T11:00:00",
        )
        assert metadata.save_name == "Test Save"
        assert metadata.save_slot == 1
        assert metadata.current_week == 3

    def test_metadata_version_default(self):
        """Test that metadata has default version."""
        metadata = SaveMetadata(
            save_name="Test",
            save_slot=1,
            game_id="test",
            current_week=1,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        assert metadata.version == "0.1.0"


class TestSaveGame:
    """Tests for save_game function."""

    def test_save_game_basic(self, temp_saves_dir, sample_game_state):
        """Test basic save functionality."""
        save_path = save_game(
            sample_game_state,
            slot=1,
            save_name="Test Save",
            saves_dir=temp_saves_dir,
        )

        assert save_path.exists()
        assert save_path.name == "save_01.json"

    def test_save_game_auto_name(self, temp_saves_dir, sample_game_state):
        """Test save with auto-generated name."""
        save_game(
            sample_game_state,
            slot=2,
            saves_dir=temp_saves_dir,
        )

        saved = load_game(2, temp_saves_dir)
        # Name should include company name and week
        assert "Test Company" in saved.metadata.save_name
        assert "Week 1" in saved.metadata.save_name

    def test_save_game_invalid_slot(self, temp_saves_dir, sample_game_state):
        """Test save with invalid slot number."""
        with pytest.raises(SaveError, match="slot must be >= 1"):
            save_game(sample_game_state, slot=0, saves_dir=temp_saves_dir)

    def test_save_game_overwrites(self, temp_saves_dir, sample_game_state):
        """Test that saving to same slot overwrites."""
        save_game(
            sample_game_state,
            slot=1,
            save_name="First Save",
            saves_dir=temp_saves_dir,
        )

        # Update state and save again
        company = sample_game_state.get_company(1)
        company = company.model_copy(update={"total_costs": 1000.0})
        updated_state = sample_game_state.update_company(company)

        save_game(
            updated_state,
            slot=1,
            save_name="Updated Save",
            saves_dir=temp_saves_dir,
        )

        saved = load_game(1, temp_saves_dir)
        assert saved.metadata.save_name == "Updated Save"
        assert saved.game_state.get_company(1).total_costs == 1000.0

    def test_save_game_preserves_created_at(self, temp_saves_dir, sample_game_state):
        """Test that updating a save preserves created_at."""
        save_game(sample_game_state, slot=1, saves_dir=temp_saves_dir)
        first_save = load_game(1, temp_saves_dir)
        created_at = first_save.metadata.created_at

        # Save again
        save_game(sample_game_state, slot=1, saves_dir=temp_saves_dir)
        second_save = load_game(1, temp_saves_dir)

        assert second_save.metadata.created_at == created_at
        assert second_save.metadata.updated_at >= created_at


class TestLoadGame:
    """Tests for load_game function."""

    def test_load_game_basic(self, temp_saves_dir, sample_game_state):
        """Test basic load functionality."""
        save_game(sample_game_state, slot=1, saves_dir=temp_saves_dir)

        saved = load_game(1, temp_saves_dir)

        assert isinstance(saved, SavedGame)
        assert saved.game_state.game_id == "test-game-001"
        assert saved.game_state.get_company(1).name == "Test Company"

    def test_load_game_not_found(self, temp_saves_dir):
        """Test loading non-existent save."""
        with pytest.raises(LoadError, match="No save found"):
            load_game(99, temp_saves_dir)

    def test_load_game_corrupt(self, temp_saves_dir):
        """Test loading corrupt save file."""
        save_path = get_save_path(1, temp_saves_dir)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w") as f:
            f.write("not valid json {{{")

        with pytest.raises(LoadError, match="Corrupt"):
            load_game(1, temp_saves_dir)

    def test_load_game_from_path(self, temp_saves_dir, sample_game_state):
        """Test loading from specific path."""
        custom_path = temp_saves_dir / "custom_save.json"
        save_game(sample_game_state, slot=1, saves_dir=temp_saves_dir)

        # Copy to custom location
        save_path = get_save_path(1, temp_saves_dir)
        import shutil

        shutil.copy(save_path, custom_path)

        saved = load_game_from_path(custom_path)
        assert saved.game_state.game_id == "test-game-001"


class TestAutosave:
    """Tests for autosave functionality."""

    def test_autosave_basic(self, temp_saves_dir, sample_game_state):
        """Test basic autosave."""
        path = autosave(sample_game_state, saves_dir=temp_saves_dir)

        assert path.exists()
        assert path.name == "autosave.json"

    def test_load_autosave(self, temp_saves_dir, sample_game_state):
        """Test loading autosave."""
        autosave(sample_game_state, saves_dir=temp_saves_dir)

        saved = load_autosave(temp_saves_dir)
        assert saved.game_state.game_id == "test-game-001"
        assert "Autosave" in saved.metadata.save_name

    def test_autosave_no_autosave(self, temp_saves_dir):
        """Test loading when no autosave exists."""
        with pytest.raises(LoadError, match="No autosave"):
            load_autosave(temp_saves_dir)

    def test_has_autosave(self, temp_saves_dir, sample_game_state):
        """Test checking for autosave existence."""
        assert not has_autosave(temp_saves_dir)

        autosave(sample_game_state, saves_dir=temp_saves_dir)
        assert has_autosave(temp_saves_dir)

    def test_delete_autosave(self, temp_saves_dir, sample_game_state):
        """Test deleting autosave."""
        autosave(sample_game_state, saves_dir=temp_saves_dir)
        assert has_autosave(temp_saves_dir)

        result = delete_autosave(temp_saves_dir)
        assert result is True
        assert not has_autosave(temp_saves_dir)

    def test_delete_autosave_not_exists(self, temp_saves_dir):
        """Test deleting non-existent autosave."""
        result = delete_autosave(temp_saves_dir)
        assert result is False


class TestDeleteSave:
    """Tests for delete_save function."""

    def test_delete_save_basic(self, temp_saves_dir, sample_game_state):
        """Test basic delete."""
        save_game(sample_game_state, slot=1, saves_dir=temp_saves_dir)
        save_path = get_save_path(1, temp_saves_dir)
        assert save_path.exists()

        result = delete_save(1, temp_saves_dir)
        assert result is True
        assert not save_path.exists()

    def test_delete_save_not_exists(self, temp_saves_dir):
        """Test deleting non-existent save."""
        result = delete_save(99, temp_saves_dir)
        assert result is False


class TestListSaves:
    """Tests for list_saves function."""

    def test_list_saves_empty(self, temp_saves_dir):
        """Test listing when no saves exist."""
        saves = list_saves(temp_saves_dir)
        assert saves == []

    def test_list_saves_multiple(self, temp_saves_dir, sample_game_state, sample_game_state_advanced):
        """Test listing multiple saves."""
        save_game(sample_game_state, slot=1, saves_dir=temp_saves_dir)
        save_game(sample_game_state_advanced, slot=2, saves_dir=temp_saves_dir)
        autosave(sample_game_state, saves_dir=temp_saves_dir)

        saves = list_saves(temp_saves_dir)

        assert len(saves) == 3
        # Should be sorted by updated_at (most recent first)
        assert all(isinstance(s, SaveMetadata) for s in saves)

    def test_list_saves_skips_corrupt(self, temp_saves_dir, sample_game_state):
        """Test that list_saves skips corrupt files."""
        save_game(sample_game_state, slot=1, saves_dir=temp_saves_dir)

        # Create corrupt file
        corrupt_path = temp_saves_dir / "save_02.json"
        with open(corrupt_path, "w") as f:
            f.write("corrupt")

        saves = list_saves(temp_saves_dir)
        assert len(saves) == 1


class TestGetSaveInfo:
    """Tests for get_save_info function."""

    def test_get_save_info_exists(self, temp_saves_dir, sample_game_state):
        """Test getting info for existing save."""
        save_game(sample_game_state, slot=1, saves_dir=temp_saves_dir)

        info = load_game(1, temp_saves_dir).metadata
        assert info.game_id == "test-game-001"
        assert info.save_slot == 1

    def test_get_save_info_not_exists(self, temp_saves_dir):
        """Test getting info for non-existent save."""
        from prosim.io.state_io import get_save_info

        info = get_save_info(99, temp_saves_dir)
        assert info is None


class TestExportImport:
    """Tests for export and import functionality."""

    def test_export_save(self, temp_saves_dir, sample_game_state):
        """Test exporting a save."""
        save_game(sample_game_state, slot=1, saves_dir=temp_saves_dir)

        export_path = temp_saves_dir / "exported.json"
        export_save(1, export_path, temp_saves_dir)

        assert export_path.exists()
        # Verify exported file is valid
        saved = load_game_from_path(export_path)
        assert saved.game_state.game_id == "test-game-001"

    def test_export_save_not_found(self, temp_saves_dir):
        """Test exporting non-existent save."""
        with pytest.raises(LoadError):
            export_save(99, temp_saves_dir / "out.json", temp_saves_dir)

    def test_import_save(self, temp_saves_dir, sample_game_state):
        """Test importing a save."""
        # Create a save file to import
        save_game(sample_game_state, slot=1, saves_dir=temp_saves_dir)
        source_path = get_save_path(1, temp_saves_dir)

        # Create another temp dir for import target
        with tempfile.TemporaryDirectory() as other_dir:
            other_path = Path(other_dir)
            metadata = import_save(source_path, slot=5, saves_dir=other_path)

            assert metadata.save_slot == 5
            # Verify we can load it
            saved = load_game(5, other_path)
            assert saved.game_state.game_id == "test-game-001"

    def test_import_invalid_file(self, temp_saves_dir):
        """Test importing invalid file."""
        invalid_path = temp_saves_dir / "invalid.json"
        with open(invalid_path, "w") as f:
            f.write("{}")

        with pytest.raises(LoadError, match="Invalid"):
            import_save(invalid_path, slot=1, saves_dir=temp_saves_dir)


class TestSavePathFunctions:
    """Tests for path helper functions."""

    def test_get_save_path(self, temp_saves_dir):
        """Test save path generation."""
        path = get_save_path(1, temp_saves_dir)
        assert path.name == "save_01.json"
        assert path.parent == temp_saves_dir

    def test_get_save_path_double_digit(self, temp_saves_dir):
        """Test save path with double-digit slot."""
        path = get_save_path(12, temp_saves_dir)
        assert path.name == "save_12.json"

    def test_get_autosave_path(self, temp_saves_dir):
        """Test autosave path generation."""
        path = get_autosave_path(temp_saves_dir)
        assert path.name == "autosave.json"


class TestIntegration:
    """Integration tests for state persistence."""

    def test_full_save_load_cycle(self, temp_saves_dir, sample_game_state):
        """Test complete save/load cycle preserves all data."""
        # Save
        save_game(
            sample_game_state,
            slot=1,
            save_name="Integration Test",
            saves_dir=temp_saves_dir,
        )

        # Load
        saved = load_game(1, temp_saves_dir)

        # Verify all state preserved
        assert saved.game_state.game_id == sample_game_state.game_id
        assert saved.game_state.current_week == sample_game_state.current_week
        assert saved.game_state.max_weeks == sample_game_state.max_weeks
        assert saved.game_state.random_seed == sample_game_state.random_seed

        company_original = sample_game_state.get_company(1)
        company_loaded = saved.game_state.get_company(1)
        assert company_loaded.name == company_original.name
        assert company_loaded.company_id == company_original.company_id

    def test_save_with_config(self, temp_saves_dir, sample_game_state):
        """Test saving with custom config."""
        from prosim.config.schema import ProsimConfig

        config = ProsimConfig()

        save_game(
            sample_game_state,
            slot=1,
            config=config,
            saves_dir=temp_saves_dir,
        )

        saved = load_game(1, temp_saves_dir)
        assert saved.config is not None
        assert saved.config.production.reject_rate == config.production.reject_rate

    def test_multiple_slots(self, temp_saves_dir, sample_game_state, sample_game_state_advanced):
        """Test using multiple save slots."""
        save_game(sample_game_state, slot=1, saves_dir=temp_saves_dir)
        save_game(sample_game_state_advanced, slot=2, saves_dir=temp_saves_dir)
        save_game(sample_game_state, slot=3, saves_dir=temp_saves_dir)

        saved1 = load_game(1, temp_saves_dir)
        saved2 = load_game(2, temp_saves_dir)
        saved3 = load_game(3, temp_saves_dir)

        assert saved1.game_state.game_id == "test-game-001"
        assert saved2.game_state.game_id == "test-game-002"
        assert saved3.game_state.game_id == "test-game-001"
