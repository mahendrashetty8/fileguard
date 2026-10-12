"""Scan command for FileGuard CLI.

Discovers and inspects files in a directory and reports category breakdown statistics.
"""

import argparse
from pathlib import Path

from fileguard import exit_codes
from fileguard.services.file_scanner import FileScanner
from fileguard.utils.formatter import (
    format_empty_directory,
    format_scan_result,
)
from fileguard.utils.logger import get_logger


def execute_scan(args: argparse.Namespace) -> int:
    """Execute the scan command with the given CLI arguments.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code indicating success or error.
    """
    logger = get_logger()
    logger.verbose = getattr(args, "verbose", False)

    target_path = Path(args.directory)
    logger.info(f"Scanning directory: {target_path}")

    scanner = FileScanner()
    result = scanner.scan(target_path)

    logger.info(f"Discovered {result.total_files} file(s) and {result.total_directories} director(y/ies).")

    if result.total_files == 0:
        print(format_empty_directory())
        return exit_codes.SUCCESS

    # Display friendly relative or clean path representation
    display_path = str(args.directory)
    print(
        format_scan_result(
            directory=display_path,
            files_found=result.total_files,
            directories_found=result.total_directories,
            category_counts=result.category_counts,
        )
    )
    return exit_codes.SUCCESS
