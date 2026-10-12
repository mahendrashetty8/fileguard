"""Validate command for FileGuard CLI.

Performs non-destructive pre-flight checks on a directory to identify potential
permission issues, conflicts, and scanning obstacles before organizing.
"""

import argparse
from pathlib import Path

from fileguard import exit_codes
from fileguard.services.file_validator import FileValidator
from fileguard.utils.formatter import (
    format_validation_failure,
    format_validation_success,
)
from fileguard.utils.logger import get_logger


def execute_validate(args: argparse.Namespace) -> int:
    """Execute the validate command with the given CLI arguments.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code indicating validation status (0 for success, 1 for problems found).
    """
    logger = get_logger()
    logger.verbose = getattr(args, "verbose", False)

    target_path = Path(args.directory)
    logger.info(f"Validating directory: {target_path}")

    validator = FileValidator()
    result = validator.validate(target_path)

    display_path = str(args.directory)

    if result.is_valid:
        print(
            format_validation_success(
                directory=display_path,
                checks=result.successful_checks,
            )
        )
        return exit_codes.SUCCESS
    else:
        print(
            format_validation_failure(
                directory=display_path,
                problems=result.problems,
            )
        )
        return exit_codes.GENERAL_ERROR
