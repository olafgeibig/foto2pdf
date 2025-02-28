"""Tests for the command-line interface."""

from pathlib import Path

import pytest
from PIL import Image

from foto2pdf.cli import main


@pytest.fixture
def sample_images(tmp_path: Path) -> Path:
    """Create a directory with sample images."""
    image_dir = tmp_path / "images"
    image_dir.mkdir()

    # Create some test images
    for i in range(3):
        image_path = image_dir / f"test_{i}.png"
        image = Image.new('RGB', (100, 100), color=f'#{i*20:02x}{i*20:02x}{i*20:02x}')
        image.save(image_path)

    return image_dir


def test_cli_basic(sample_images: Path, tmp_path: Path) -> None:
    """Test basic CLI functionality."""
    output_dir = tmp_path / "output"

    # Run CLI with basic arguments
    result = main([
        str(sample_images),
        str(output_dir),
        "--log-level=ERROR",
    ])

    assert result == 0  # Should succeed
    assert output_dir.exists()
    assert len(list(output_dir.glob("processed_*.png"))) == 3


def test_cli_custom_params(sample_images: Path, tmp_path: Path) -> None:
    """Test CLI with custom parameters."""
    output_dir = tmp_path / "output"

    # Run CLI with all optional parameters
    result = main([
        str(sample_images),
        str(output_dir),
        "--prefix=custom_",
        "--margin=10",
        "--landscape",
        "--workers=2",
        "--log-level=ERROR",
    ])

    assert result == 0  # Should succeed
    assert output_dir.exists()
    assert len(list(output_dir.glob("custom_*.png"))) == 3


def test_cli_nonexistent_input() -> None:
    """Test CLI with non-existent input directory."""
    result = main([
        "/nonexistent/path",
        "/tmp/output",
        "--log-level=ERROR",
    ])

    assert result != 0  # Should fail


def test_cli_invalid_margin(sample_images: Path, tmp_path: Path) -> None:
    """Test CLI with invalid margin value."""
    output_dir = tmp_path / "output"

    result = main([
        str(sample_images),
        str(output_dir),
        "--margin=101",  # Invalid margin
        "--log-level=ERROR",
    ])

    assert result != 0  # Should fail


def test_cli_help(capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI help output."""
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Process photos to prepare them for PDF conversion" in captured.out
