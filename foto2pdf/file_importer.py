"""Module for scanning directories and finding image files."""

import logging
from pathlib import Path
from typing import Iterator, Set

# Set up logging
logger = logging.getLogger(__name__)

# Supported image extensions
SUPPORTED_EXTENSIONS: Set[str] = {".jpg", ".jpeg", ".png"}


def find_image_files(directory: str | Path) -> list[Path]:
    """
    Recursively scan a directory for image files.

    Args:
        directory: Path to the directory to scan. Can be a string or Path object.

    Returns:
        A list of Path objects pointing to image files.

    Raises:
        ValueError: If the directory does not exist or is not a directory.
    """
    directory_path = Path(directory)
    
    if not directory_path.exists():
        raise ValueError(f"Directory does not exist: {directory}")
    if not directory_path.is_dir():
        raise ValueError(f"Path is not a directory: {directory}")

    logger.info(f"Scanning directory: {directory_path}")
    
    def _scan_directory() -> Iterator[Path]:
        """Helper generator to scan directory for image files."""
        for file_path in directory_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                logger.debug(f"Found image file: {file_path}")
                yield file_path
    
    # Convert iterator to list for easier handling
    image_files = list(_scan_directory())
    logger.info(f"Found {len(image_files)} image files")
    
    return sorted(image_files)  # Sort for consistent ordering
