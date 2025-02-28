"""Tests for the batch_processor module."""

from pathlib import Path

import pytest
from PIL import Image

from foto2pdf.batch_processor import (
    BatchProcessingResult,
    get_batch_summary,
    process_images,
)


@pytest.fixture
def image_dir(tmp_path: Path) -> Path:
    """Create a directory with test images."""
    image_dir = tmp_path / "images"
    image_dir.mkdir()

    # Create valid images
    for i in range(3):
        image_path = image_dir / f"test_{i}.png"
        image = Image.new('RGB', (100, 100), color=f'#{i*20:02x}{i*20:02x}{i*20:02x}')
        image.save(image_path)

    # Create an invalid image file
    invalid_path = image_dir / "invalid.png"
    invalid_path.write_text("This is not an image file")

    return image_dir


@pytest.fixture
def nested_image_dir(tmp_path: Path) -> Path:
    """Create a directory with nested test images."""
    root_dir = tmp_path / "nested"
    root_dir.mkdir()

    # Create images in root
    image = Image.new('RGB', (100, 100), color='red')
    image.save(root_dir / "root.png")

    # Create images in subdirectories
    for subdir in ['a', 'b/c']:
        subdir_path = root_dir / subdir
        subdir_path.mkdir(parents=True)
        image = Image.new('RGB', (100, 100), color='blue')
        image.save(subdir_path / "nested.png")

    return root_dir


def test_process_images(image_dir: Path, tmp_path: Path) -> None:
    """Test processing multiple images."""
    output_dir = tmp_path / "output"

    # Process images and collect results
    results = list(process_images(image_dir, output_dir))

    # Check number of results
    assert len(results) == 4  # 3 valid + 1 invalid images

    # Count successes and failures
    successes = [r for r in results if r.success]
    failures = [r for r in results if not r.success]

    assert len(successes) == 3
    assert len(failures) == 1

    # Check that output files exist
    for result in successes:
        assert result.output_path is not None
        assert result.output_path.exists()
        assert result.output_path.name.startswith("processed_")

    # Check that failed result has error
    assert all(r.error is not None for r in failures)


def test_process_images_nested(nested_image_dir: Path, tmp_path: Path) -> None:
    """Test processing images in nested directories."""
    output_dir = tmp_path / "output"

    # Process images
    results = list(process_images(nested_image_dir, output_dir))

    # Should find 3 images total
    assert len(results) == 3
    assert all(r.success for r in results)

    # Check that output directory structure matches input
    assert (output_dir / "processed_root.png").exists()
    assert (output_dir / "processed_nested.png").exists()


def test_process_images_nonexistent_dir(tmp_path: Path) -> None:
    """Test processing images from a non-existent directory."""
    with pytest.raises(FileNotFoundError):
        list(process_images(tmp_path / "nonexistent", tmp_path / "output"))


def test_process_images_not_a_dir(tmp_path: Path) -> None:
    """Test processing images when input is not a directory."""
    file_path = tmp_path / "file.txt"
    file_path.touch()

    with pytest.raises(NotADirectoryError):
        list(process_images(file_path, tmp_path / "output"))


def test_process_images_custom_params(image_dir: Path, tmp_path: Path) -> None:
    """Test processing images with custom parameters."""
    output_dir = tmp_path / "output"

    # Process with custom parameters
    results = list(process_images(
        image_dir,
        output_dir,
        prefix="custom_",
        margin_percent=10.0,
        force_portrait=False
    ))

    successes = [r for r in results if r.success]
    assert len(successes) > 0
    
    # Check that custom prefix was used
    for result in successes:
        assert result.output_path is not None
        assert result.output_path.name.startswith("custom_")


def test_get_batch_summary() -> None:
    """Test generating batch processing summary."""
    # Create sample results
    results = [
        BatchProcessingResult(
            input_path=Path("success1.jpg"),
            output_path=Path("out1.png"),
            processing_info=None
        ),
        BatchProcessingResult(
            input_path=Path("success2.jpg"),
            output_path=Path("out2.png"),
            processing_info=None
        ),
        BatchProcessingResult(
            input_path=Path("invalid.jpg"),
            output_path=None,
            processing_info=None,
            error=ValueError("Test error")
        ),
    ]

    summary = get_batch_summary(results)

    assert summary["total"] == 3
    assert summary["success"] == 2
    assert summary["errored"] == 1
    assert summary["error_types"]["ValueError"] == 1
