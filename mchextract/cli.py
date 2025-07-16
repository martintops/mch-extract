"""
Command-line interface for mch-extract.

This module provides the command-line interface functionality,
using the API module for actual data extraction.
"""

import logging
import sys
from pathlib import Path

from .api import MchExtract
from .commandline import parse_args
from .logging_config import setup_logging
from .metadata_downloader import MetaDataDownloader
from .metadata_loader import MetaDataLoader


def main() -> int:
    """
    Main entry point for the command-line interface.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Initialize variables that might be used in exception handling
    logger = logging.getLogger(__name__)
    verbose = False

    try:
        # We need to parse args twice: once to get verbose setting, once for full parsing
        # First pass just to get verbose flag
        import argparse

        temp_parser = argparse.ArgumentParser(add_help=False)
        temp_parser.add_argument("--verbose", "-v", action="store_true")
        temp_args, _ = temp_parser.parse_known_args()
        verbose = temp_args.verbose

        # Set up logging with verbose setting
        setup_logging(verbose=verbose)

        # Load metadata for argument parsing
        logger.debug("Loading metadata for argument validation...")
        manager = MetaDataDownloader()
        manager.ensure_data_available()
        loader = MetaDataLoader()
        metadata = loader.load_all()

        # Parse command line arguments
        args = parse_args(metadata)

        # Create API instance
        extractor = MchExtract(verbose=args.verbose)

        logger.debug(
            f"Extracting {args.timescale.to_readable_name()} data from {args.start_date} to {args.end_date} "
            f"for stations {args.stations} with variables {args.variables}."
        )

        # Extract data using the API
        data = extractor.get_data(
            stations=args.stations,
            variables=args.variables,
            start_date=args.start_date,
            end_date=args.end_date,
            timescale=args.timescale,
            dwh_parameters=args.parameters,
        )

        # Determine output format based on file extension
        if args.output is not None:
            output_path = Path(args.output)
            output_format = output_path.suffix.lower().replace(".", "")

            match output_format:
                case "csv":
                    data.write_csv(output_path)
                case "parquet":
                    data.write_parquet(output_path)
                case "json":
                    data.write_json(output_path)
                case _:
                    logger.warning(
                        f"Unsupported output format: {output_format}. Defaulting to CSV."
                    )
                    data.write_csv(output_path)
        else:
            # If no output specified, just print the data to stdout
            print(data.write_csv())

        logger.debug(
            f"Data extraction completed successfully. Output saved to {args.output}"
        )

        return 0

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        if verbose:
            logger.exception("Full traceback:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
