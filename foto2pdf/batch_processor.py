"""Batch processing functionality for foto2pdf."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

from PIL import Image, UnidentifiedImageError

from foto2pdf.file_importer import find_image_files
from foto2pdf.image_processor import ProcessingInfo, process_image

logger = logging.getLogger(__name__)


@dataclass
class BatchProcessingResult:
    """Result of processing a single image in a batch."""
    input_path: Path
    output_path: Path | None
    processing_info: ProcessingInfo | None
    error: Exception | None = None

    @property
    def success(self) -> bool:
        """Return True if the processing was successful."""
        return self.error is None and self.output_path is not None


def process_images(
    input_dir: str | Path,
    output_dir: str | Path,
    prefix: str = "processed_",
    max_workers: int | None = None,
    **process_kwargs,
) -> Iterator[BatchProcessingResult]:
    """
    Process all images in a directory and save them to an output directory.

    Args:
        input_dir: Directory containing images to process
        output_dir: Directory to save processed images to
        prefix: Prefix to add to processed image filenames
        max_workers: Maximum number of worker threads for parallel processing.
            If None, uses the default from ThreadPoolExecutor.
        **process_kwargs: Additional keyword arguments to pass to process_image

    Yields:
        BatchProcessingResult objects containing the results of processing each image

    Raises:
        FileNotFoundError: If input_dir does not exist
        NotADirectoryError: If input_dir is not a directory
        PermissionError: If output_dir cannot be created or written to
    """
    # Convert paths to Path objects
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # Validate input directory
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory not found: {input_path}")
    if not input_path.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {input_path}")

    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)

    # Find all image files
    image_files = find_image_files(input_path)
    logger.info(f"Found {len(image_files)} images to process")

    def process_single_image(image_path: Path) -> BatchProcessingResult:
        """Process a single image and return the result."""
        # Determine output path
        rel_path = image_path.relative_to(input_path)
        output_file = output_path / f"{prefix}{rel_path.name}"
        output_file = output_file.with_suffix(".png")  # Use PNG for processed images

        try:
            # Process the image
            processed_image, processing_info = process_image(
                image_path, **process_kwargs
            )

            # Ensure output directory exists (for nested directories)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Save the processed image
            processed_image.save(output_file, "PNG")
            logger.info(f"Saved processed image to {output_file}")

            return BatchProcessingResult(
                input_path=image_path,
                output_path=output_file,
                processing_info=processing_info,
                error=None
            )

        except Exception as e:
            logger.error(f"Error processing {image_path}: {e}")
            return BatchProcessingResult(
                input_path=image_path,
                output_path=None,
                processing_info=None,
                error=e
            )

    # Process images in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_path = {
            executor.submit(process_single_image, path): path
            for path in image_files
        }

        # Yield results as they complete
        for future in as_completed(future_to_path):
            yield future.result()


def get_batch_summary(results: Iterable[BatchProcessingResult]) -> dict:
    """
    Generate a summary of batch processing results.

    Args:
        results: Iterable of BatchProcessingResult objects

    Returns:
        Dictionary containing summary statistics
    """
    total = success = skipped = errored = 0
    error_types: dict[str, int] = {}

    for result in results:
        total += 1
        if result.success:
            success += 1
        elif isinstance(result.error, UnidentifiedImageError):
            skipped += 1
        else:
            errored += 1
            error_type = type(result.error).__name__
            error_types[error_type] = error_types.get(error_type, 0) + 1

    return {
        "total": total,
        "success": success,
        "skipped": skipped,
        "errored": errored,
        "error_types": error_types,
    }
