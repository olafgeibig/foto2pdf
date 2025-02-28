"""Tests for the image_processor module."""

from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw, UnidentifiedImageError

from foto2pdf.image_processor import (
    load_image,
    deskew_image,
    crop_to_a4,
    ImageInfo,
    A4_RATIO,
    process_image,
    ProcessingInfo,
)


@pytest.fixture
def sample_image(tmp_path: Path) -> Path:
    """Create a sample test image."""
    image_path = tmp_path / "test.png"
    
    # Create a small test image
    image = Image.new('RGB', (100, 100), color='red')
    image.save(image_path)
    
    return image_path


@pytest.fixture
def wide_image(tmp_path: Path) -> Path:
    """Create a wide test image."""
    image_path = tmp_path / "wide.png"
    
    # Create a wide image (2:1 aspect ratio)
    image = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(image)
    
    # Add some content
    draw.rectangle([50, 50, 350, 150], fill='black')
    draw.text((175, 90), "Wide Image", fill='white')
    
    image.save(image_path)
    return image_path


@pytest.fixture
def tall_image(tmp_path: Path) -> Path:
    """Create a tall test image."""
    image_path = tmp_path / "tall.png"
    
    # Create a tall image (1:2 aspect ratio)
    image = Image.new('RGB', (200, 400), color='white')
    draw = ImageDraw.Draw(image)
    
    # Add some content
    draw.rectangle([50, 50, 150, 350], fill='black')
    draw.text((70, 190), "Tall", fill='white', rotation=90)
    
    image.save(image_path)
    return image_path


@pytest.fixture
def skewed_image(tmp_path: Path) -> tuple[Path, float]:
    """Create a skewed test image with known angle."""
    image_path = tmp_path / "skewed.png"
    
    # Create a test image with multiple parallel lines for better skew detection
    width, height = 400, 400
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # Draw multiple parallel lines at a known angle
    angle = 15.0  # degrees
    line_spacing = 40
    line_length = 300
    center_y = height // 2
    
    for offset in range(-200, 201, line_spacing):
        # Calculate rotated line coordinates
        rad = np.radians(angle)
        dx = (line_length / 2) * np.cos(rad)
        dy = (line_length / 2) * np.sin(rad)
        
        y = center_y + offset
        start = (int(width/2 - dx), int(y - dy))
        end = (int(width/2 + dx), int(y + dy))
        
        # Draw thick black line
        draw.line([start, end], fill='black', width=2)
    
    # Add some text for additional features
    draw.text((50, 50), "Test Text", fill='black')
    
    image.save(image_path)
    return image_path, angle


@pytest.fixture
def invalid_image(tmp_path: Path) -> Path:
    """Create an invalid image file."""
    invalid_path = tmp_path / "invalid.png"
    invalid_path.write_text("This is not an image file")
    return invalid_path


def test_load_image(sample_image: Path) -> None:
    """Test loading a valid image file."""
    image, info = load_image(sample_image)
    
    assert isinstance(image, Image.Image)
    assert isinstance(info, ImageInfo)
    
    assert info.filename == "test.png"
    assert info.size == (100, 100)
    assert info.format == "PNG"
    assert info.mode == "RGB"


def test_load_nonexistent_image(tmp_path: Path) -> None:
    """Test loading a non-existent image file."""
    with pytest.raises(FileNotFoundError):
        load_image(tmp_path / "nonexistent.png")


def test_load_invalid_image(invalid_image: Path) -> None:
    """Test loading an invalid image file."""
    with pytest.raises(UnidentifiedImageError):
        load_image(invalid_image)


def test_deskew_image(skewed_image: tuple[Path, float]) -> None:
    """Test deskewing an image with known skew angle."""
    image_path, original_angle = skewed_image
    image, _ = load_image(image_path)
    
    deskewed, detected_angle = deskew_image(image)
    
    assert isinstance(deskewed, Image.Image)
    assert isinstance(detected_angle, float)
    
    # The detected angle should be close to the original angle
    # Note: The sign might be different depending on the deskew implementation
    assert abs(abs(detected_angle) - original_angle) < 1.0


def test_deskew_unskewed_image(sample_image: Path) -> None:
    """Test deskewing an image that is already straight."""
    image, _ = load_image(sample_image)
    deskewed, angle = deskew_image(image)
    
    assert isinstance(deskewed, Image.Image)
    assert abs(angle) < 0.1  # Should detect very small or no angle


def test_crop_wide_image(wide_image: Path) -> None:
    """Test cropping a wide image to A4 proportions."""
    image, _ = load_image(wide_image)
    
    # Test with default settings
    cropped, crop_box = crop_to_a4(image)
    
    # Check that the cropped image has A4 proportions
    width, height = cropped.size
    assert abs(height / width - A4_RATIO) < 0.01
    
    # Check that the crop box is valid for the rotated image
    # Note: Since we rotate wide images to portrait, we need to swap width/height
    image_width, image_height = image.size
    if image_width > image_height:  # Was rotated to portrait
        image_width, image_height = image_height, image_width
    
    left, top, right, bottom = crop_box
    assert 0 <= left < right <= image_width
    assert 0 <= top < bottom <= image_height


def test_crop_tall_image(tall_image: Path) -> None:
    """Test cropping a tall image to A4 proportions."""
    image, _ = load_image(tall_image)
    
    # Test with different margin
    cropped, crop_box = crop_to_a4(image, margin_percent=10.0)
    
    # Check that the cropped image has A4 proportions
    width, height = cropped.size
    assert abs(height / width - A4_RATIO) < 0.01
    
    # Check that the crop box is valid
    left, top, right, bottom = crop_box
    assert 0 <= left < right <= image.width
    assert 0 <= top < bottom <= image.height


def test_crop_with_rotation(wide_image: Path) -> None:
    """Test cropping with automatic rotation to portrait."""
    image, _ = load_image(wide_image)
    
    # Test with force_portrait=True (default)
    cropped, _ = crop_to_a4(image)
    width, height = cropped.size
    assert height > width  # Should be in portrait orientation
    
    # Test with force_portrait=False
    cropped, _ = crop_to_a4(image, force_portrait=False)
    width, height = cropped.size
    assert width > height  # Should maintain landscape orientation


def test_process_image(sample_image: Path) -> None:
    """Test the complete image processing pipeline."""
    # Process the image with default settings
    processed, info = process_image(sample_image)
    
    # Check processed image
    assert isinstance(processed, Image.Image)
    assert processed.size[0] > 0
    assert processed.size[1] > 0
    
    # Check processing info
    assert isinstance(info, ProcessingInfo)
    assert isinstance(info.original_info, ImageInfo)
    assert isinstance(info.skew_angle, float)
    assert len(info.crop_box) == 4
    assert len(info.final_size) == 2
    
    # Check that the final size matches the processed image
    assert processed.size == info.final_size


def test_process_image_with_params(skewed_image: tuple[Path, float]) -> None:
    """Test the image processing pipeline with custom parameters."""
    image_path, expected_angle = skewed_image
    
    # Process the image with custom parameters
    processed, info = process_image(
        image_path,
        margin_percent=10.0,
        force_portrait=False,
        deskew_params={"num_peaks": 20}
    )
    
    # Check that the skew angle is close to the expected angle
    # Note: The sign might be different depending on the deskew implementation
    assert abs(abs(info.skew_angle) - expected_angle) < 1.0
    
    # Check that margin was applied (final size should be smaller)
    assert processed.size[0] < info.original_info.size[0]
    assert processed.size[1] < info.original_info.size[1]


def test_process_image_invalid_margin() -> None:
    """Test processing with invalid margin percentage."""
    with pytest.raises(ValueError):
        process_image("dummy.jpg", margin_percent=101.0)
