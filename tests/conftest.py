"""
Pytest configuration and fixtures for PROSIM tests.
"""

from pathlib import Path

import pytest

# Path to archive data for validation tests
ARCHIVE_PATH = Path(__file__).parent.parent / "archive"
DATA_PATH = ARCHIVE_PATH / "data"


@pytest.fixture
def archive_path() -> Path:
    """Return path to archive directory."""
    return ARCHIVE_PATH


@pytest.fixture
def data_path() -> Path:
    """Return path to archived data files."""
    return DATA_PATH


@pytest.fixture
def sample_decs_file(data_path: Path) -> Path:
    """Return path to a sample DECS file."""
    return data_path / "DECS14.DAT"


@pytest.fixture
def sample_rept_file(data_path: Path) -> Path:
    """Return path to a sample REPT file."""
    return data_path / "REPT14.DAT"


@pytest.fixture
def human_readable_report(data_path: Path) -> Path:
    """Return path to human-readable report (week1.txt)."""
    return data_path / "week1.txt"
