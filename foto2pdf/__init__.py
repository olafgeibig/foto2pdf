"""foto2pdf - A tool for processing and converting photos to PDF."""

from foto2pdf.batch_processor import (
    BatchProcessingResult,
    get_batch_summary,
    process_images,
)
from foto2pdf.file_importer import find_image_files
from foto2pdf.image_processor import (
    ImageInfo,
    ProcessingInfo,
    load_image,
    deskew_image,
    crop_to_a4,
    process_image,
)

__all__ = [
    "find_image_files",
    "ImageInfo",
    "ProcessingInfo",
    "BatchProcessingResult",
    "load_image",
    "deskew_image",
    "crop_to_a4",
    "process_image",
    "process_images",
    "get_batch_summary",
]
__version__ = "0.1.0"
