"""Module for loading and processing images."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, UnidentifiedImageError
from deskew import determine_skew

# Set up logging
logger = logging.getLogger(__name__)

# Standard A4 paper size in pixels at 300 DPI
A4_WIDTH_PX = int(8.27 * 300)  # 8.27 inches * 300 DPI
A4_HEIGHT_PX = int(11.69 * 300)  # 11.69 inches * 300 DPI
A4_RATIO = A4_HEIGHT_PX / A4_WIDTH_PX


@dataclass
class ImageInfo:
    """Container for image metadata."""
    filename: str
    size: tuple[int, int]
    format: str
    mode: str
    skew_angle: float | None = None
    crop_box: tuple[int, int, int, int] | None = None


def load_image(file_path: str | Path) -> tuple[Image.Image, ImageInfo]:
    """
    Load an image file and return both the image and its metadata.

    Args:
        file_path: Path to the image file.

    Returns:
        A tuple containing:
            - The loaded PIL Image object
            - ImageInfo object containing metadata about the image

    Raises:
        FileNotFoundError: If the image file does not exist
        UnidentifiedImageError: If the file is not a valid image
        OSError: If there's an error reading the file
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {path}")
    
    try:
        image = Image.open(path)
        
        # Force load the image data to catch potential errors early
        image.load()
        
        info = ImageInfo(
            filename=path.name,
            size=image.size,
            format=image.format or "unknown",
            mode=image.mode
        )
        
        logger.info(
            f"Loaded image: {info.filename} "
            f"(size: {info.size}, format: {info.format}, mode: {info.mode})"
        )
        
        return image, info
        
    except UnidentifiedImageError:
        logger.error(f"File is not a valid image: {path}")
        raise
    except OSError as e:
        logger.error(f"Error reading image file {path}: {e}")
        raise


def deskew_image(
    image: Image.Image,
    num_peaks: int = 20,
    min_angle: float = -45,
    max_angle: float = 45,
    min_deviation: float = 1.0,
) -> tuple[Image.Image, float]:
    """
    Deskew an image by detecting and correcting its skew angle.

    Args:
        image: PIL Image object to deskew
        num_peaks: Number of peaks to consider in the Hough transform
        min_angle: Minimum angle to consider for deskewing (degrees)
        max_angle: Maximum angle to consider for deskewing (degrees)
        min_deviation: Minimum deviation to consider for deskewing

    Returns:
        A tuple containing:
            - The deskewed PIL Image object
            - The detected skew angle in degrees

    Note:
        The image will be converted to grayscale temporarily for skew detection,
        but the original color image will be rotated and returned.
    """
    # Convert to grayscale for skew detection
    grayscale = image.convert('L')
    
    # Convert to numpy array for deskew library
    np_image = np.array(grayscale)
    
    # Determine the skew angle with fine-tuned parameters
    angle = determine_skew(
        np_image,
        num_peaks=num_peaks,
        min_angle=min_angle,
        max_angle=max_angle,
        min_deviation=min_deviation
    )
    
    if angle is None:
        logger.info("No skew detected in image")
        return image, 0.0
    
    logger.info(f"Detected skew angle: {angle:.2f} degrees")
    
    if abs(angle) < 0.1:
        logger.info("Skew angle too small, skipping rotation")
        return image, angle
    
    # Rotate the original image by the negative of the detected angle
    # expand=True ensures the entire rotated image is visible
    # fillcolor='white' fills any new pixels created during rotation
    rotated = image.rotate(-angle, expand=True, fillcolor='white')
    
    logger.info("Image deskewed successfully")
    return rotated, angle


def crop_to_a4(
    image: Image.Image,
    margin_percent: float = 5.0,
    force_portrait: bool = True,
    _is_recursive: bool = False
) -> tuple[Image.Image, tuple[int, int, int, int]]:
    """
    Crop an image to match A4 paper proportions.

    Args:
        image: PIL Image object to crop
        margin_percent: Percentage of margin to leave around the content (0-100)
        force_portrait: If True, ensure the output is in portrait orientation
        _is_recursive: Internal flag to prevent infinite recursion

    Returns:
        A tuple containing:
            - The cropped PIL Image object
            - The crop box used (left, top, right, bottom)

    Note:
        This function attempts to center the crop box in the image while
        maintaining A4 proportions. The crop box will be the largest possible
        that fits within the image while maintaining the A4 aspect ratio.
    """
    # Get initial dimensions and orientation
    width, height = image.size
    original_landscape = width > height
    
    # For landscape output, rotate the image first
    if not force_portrait and not _is_recursive and not original_landscape:
        # If we want landscape but have portrait, rotate to landscape
        image = image.rotate(-90, expand=True)
        width, height = image.size
    elif force_portrait and original_landscape:
        # If we want portrait but have landscape, rotate to portrait
        image = image.rotate(90, expand=True)
        width, height = image.size
    
    # Calculate target dimensions to maintain A4 ratio
    current_ratio = height / width
    target_ratio = A4_RATIO if force_portrait else (1 / A4_RATIO)
    
    if current_ratio > target_ratio:
        # Image is too tall, fit to width
        new_width = width
        new_height = int(width * target_ratio)
    else:
        # Image is too wide, fit to height
        new_height = height
        new_width = int(height / target_ratio)
    
    # Apply margin
    margin_x = int(new_width * (margin_percent / 100))
    margin_y = int(new_height * (margin_percent / 100))
    new_width -= 2 * margin_x
    new_height -= 2 * margin_y
    
    # Calculate the crop box coordinates
    left = (width - new_width) // 2
    top = (height - new_height) // 2
    right = left + new_width
    bottom = top + new_height
    
    # Ensure crop box is within image bounds
    left = max(0, left)
    top = max(0, top)
    right = min(width, right)
    bottom = min(height, bottom)
    
    # Create the crop box
    crop_box = (left, top, right, bottom)
    
    logger.info(
        f"Cropping image from {image.size} to {(new_width, new_height)} "
        f"with {margin_percent}% margin"
    )
    
    # Perform the crop
    cropped = image.crop(crop_box)
    
    return cropped, crop_box


def process_image(
    file_path: str | Path,
    margin_percent: float = 5.0,
    force_portrait: bool = True,
    deskew_params: dict | None = None,
) -> tuple[Image.Image, 'ProcessingInfo']:
    """
    Process an image through the complete pipeline: loading, deskewing, and cropping.

    Args:
        file_path: Path to the image file to process
        margin_percent: Percentage of margin to leave around the content when cropping (0-100)
        force_portrait: If True, ensure the output is in portrait orientation
        deskew_params: Optional dictionary of parameters to pass to the deskew function

    Returns:
        A tuple containing:
            - The processed PIL Image object
            - A ProcessingInfo object containing metadata about the processing steps

    Raises:
        FileNotFoundError: If the image file does not exist
        UnidentifiedImageError: If the file is not a valid image
        ValueError: If the margin_percent is not between 0 and 100
    """
    # Validate margin_percent
    if not 0 <= margin_percent <= 100:
        raise ValueError(
            f"margin_percent must be between 0 and 100, got {margin_percent}"
        )
    
    logger.info(f"Processing image: {file_path}")
    
    # Load the image
    image, image_info = load_image(file_path)
    logger.info(f"Loaded image: {image_info}")
    
    # Deskew the image
    deskew_params = deskew_params or {}
    deskewed_image, skew_angle = deskew_image(image, **deskew_params)
    logger.info(f"Deskewed image by {skew_angle:.2f} degrees")
    
    # Crop to A4 proportions
    cropped_image, crop_box = crop_to_a4(
        deskewed_image,
        margin_percent=margin_percent,
        force_portrait=force_portrait
    )
    logger.info(
        f"Cropped image from {deskewed_image.size} to {cropped_image.size} "
        f"with crop box {crop_box}"
    )
    
    # Create processing info
    processing_info = ProcessingInfo(
        original_info=image_info,
        skew_angle=skew_angle,
        crop_box=crop_box,
        final_size=cropped_image.size,
    )
    
    return cropped_image, processing_info


@dataclass
class ProcessingInfo:
    """Information about the image processing steps."""
    original_info: ImageInfo
    skew_angle: float
    crop_box: tuple[int, int, int, int]
    final_size: tuple[int, int]
