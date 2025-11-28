"""Shared pytest fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def sample_data_dir() -> Path:
    """Path to test sample data."""
    return Path(__file__).parent / "sample_data"


@pytest.fixture
def temp_upload_dir(tmp_path: Path) -> Path:
    """Temporary directory for upload tests."""
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    return upload_dir
