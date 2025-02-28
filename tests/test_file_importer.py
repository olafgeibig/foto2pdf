"""Tests for the file_importer module."""

import pytest
from pathlib import Path

from foto2pdf.file_importer import find_image_files


@pytest.fixture
def temp_image_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with some test image files."""
    # Create some test files
    (tmp_path / "test1.jpg").touch()
    (tmp_path / "test2.jpeg").touch()
    (tmp_path / "test3.png").touch()
    (tmp_path / "not_an_image.txt").touch()
    
    # Create a subdirectory with more files
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "test4.jpg").touch()
    
    return tmp_path


def test_find_image_files(temp_image_dir: Path) -> None:
    """Test finding image files in a directory."""
    image_files = find_image_files(temp_image_dir)
    
    # Should find 4 image files (3 in root, 1 in subdir)
    assert len(image_files) == 4
    
    # All files should be Path objects
    assert all(isinstance(f, Path) for f in image_files)
    
    # All files should have supported extensions
    assert all(f.suffix.lower() in {".jpg", ".jpeg", ".png"} for f in image_files)


def test_find_image_files_nonexistent_dir() -> None:
    """Test handling of non-existent directory."""
    with pytest.raises(ValueError, match="Directory does not exist"):
        find_image_files(Path("nonexistent_dir"))


def test_find_image_files_not_a_dir(tmp_path: Path) -> None:
    """Test handling of path that is not a directory."""
    file_path = tmp_path / "test.txt"
    file_path.touch()
    
    with pytest.raises(ValueError, match="Path is not a directory"):
        find_image_files(file_path)
