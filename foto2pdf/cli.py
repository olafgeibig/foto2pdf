"""Command-line interface for foto2pdf."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Sequence

from foto2pdf.batch_processor import get_batch_summary, process_images


def create_parser() -> argparse.ArgumentParser:
    """Create the command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Process photos to prepare them for PDF conversion.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "input_dir",
        type=str,
        help="Directory containing images to process",
    )
    parser.add_argument(
        "output_dir",
        type=str,
        help="Directory to save processed images",
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default="processed_",
        help="Prefix to add to processed image filenames",
    )
    parser.add_argument(
        "--margin",
        type=float,
        default=5.0,
        help="Margin percentage to leave around content (0-100)",
    )
    parser.add_argument(
        "--landscape",
        action="store_true",
        help="Allow images to remain in landscape orientation",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of worker threads for parallel processing",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """
    Main entry point for the CLI.

    Args:
        argv: Command line arguments (uses sys.argv if not provided)

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    try:
        # Convert paths
        input_path = Path(args.input_dir)
        output_path = Path(args.output_dir)

        # Process images
        logger.info(f"Processing images from {input_path}")
        logger.info(f"Saving results to {output_path}")

        results = list(process_images(
            input_dir=input_path,
            output_dir=output_path,
            prefix=args.prefix,
            margin_percent=args.margin,
            force_portrait=not args.landscape,
            max_workers=args.workers,
        ))

        # Print summary
        summary = get_batch_summary(results)
        print("\nProcessing Summary:")
        print(f"Total images processed: {summary['total']}")
        print(f"Successfully processed: {summary['success']}")
        print(f"Skipped (invalid files): {summary['skipped']}")
        print(f"Failed with errors: {summary['errored']}")

        if summary['error_types']:
            print("\nError types encountered:")
            for error_type, count in summary['error_types'].items():
                print(f"- {error_type}: {count}")

        # Return non-zero if any images failed
        return 1 if summary['errored'] > 0 else 0

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
