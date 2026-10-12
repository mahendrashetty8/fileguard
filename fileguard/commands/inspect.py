"""Inspect command handler for FileGuard CLI.

Analyzes files and directories, providing deep CSV inspection (columns, rows,
encoding, delimiter, data consistency, required column verification, and
column-by-column data profiling) as well as general file information.
"""

import argparse
from pathlib import Path

from fileguard import exit_codes
from fileguard.config import get_category_for_file
from fileguard.errors import DirectoryNotFoundError, InvalidInputError, PermissionDeniedError
from fileguard.services.csv_inspector import CSVInspector
from fileguard.utils.formatter import (
    DIVIDER,
    format_column_analysis,
    format_csv_inspection,
    format_missing_columns_error,
)
from fileguard.utils.logger import get_logger


def execute_inspect(args: argparse.Namespace) -> int:
    """Execute the inspect/info command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 or 2 for problems or missing columns).
    """
    logger = get_logger()
    logger.verbose = getattr(args, "verbose", False)

    target_path = Path(args.path)

    if not target_path.exists():
        raise DirectoryNotFoundError(
            message="Path not found.",
            path=str(args.path),
            hint="Please verify the file or directory path.",
        )

    logger.info(f"Inspecting: {target_path}")
    req_cols = getattr(args, "required_columns", None)
    analyze_cols = getattr(args, "analyze_columns", False)

    # Flatten required_columns if user passed comma-separated strings
    if req_cols:
        flattened_reqs = []
        for item in req_cols:
            parts = [p.strip() for p in item.split(",") if p.strip()]
            flattened_reqs.extend(parts)
        req_cols = flattened_reqs

    # Case 1: Target is a CSV file
    if target_path.is_file() and target_path.suffix.lower() == ".csv":
        inspector = CSVInspector()
        result = inspector.inspect(
            target_path,
            required_columns=req_cols,
            analyze_columns=analyze_cols,
        )

        # If required columns were missing, format and print error
        if result.missing_columns:
            print(
                format_missing_columns_error(
                    file_path=str(args.path),
                    missing_columns=result.missing_columns,
                    available_columns=result.columns,
                )
            )
            return exit_codes.INVALID_ARGUMENT

        # If column-by-column analysis was requested, display detailed breakdown
        if analyze_cols and result.column_analyses:
            print(
                format_column_analysis(
                    file_path=str(args.path),
                    total_rows=result.total_rows,
                    total_cols=result.column_count,
                    analyses=result.column_analyses,
                )
            )
            return exit_codes.SUCCESS if result.is_valid else exit_codes.GENERAL_ERROR

        # Default overview
        print(
            format_csv_inspection(
                file_path=str(args.path),
                columns=result.columns,
                total_rows=result.total_rows,
                delimiter=result.delimiter,
                encoding=result.encoding,
                is_valid=result.is_valid,
                problems=result.problems,
            )
        )
        return exit_codes.SUCCESS if result.is_valid else exit_codes.GENERAL_ERROR

    # Case 2: Target is a directory containing CSV files
    if target_path.is_dir():
        csv_files = [p for p in target_path.glob("*.csv") if p.is_file()]
        if csv_files:
            print("CSV Files Inspection")
            print(DIVIDER)
            print(f"\nDirectory: {args.path}")
            print(f"Found {len(csv_files)} CSV file(s):\n")

            inspector = CSVInspector()
            all_valid = True
            for csv_file in sorted(csv_files):
                res = inspector.inspect(
                    csv_file,
                    required_columns=req_cols,
                    analyze_columns=analyze_cols,
                )
                if res.missing_columns:
                    all_valid = False
                    print(f"• {csv_file.name} - [MISSING REQUIRED COLUMNS]")
                    print(f"    Missing: {', '.join(res.missing_columns)}")
                    print(f"    Available ({res.column_count}): {', '.join(res.columns[:4])}...\n")
                else:
                    status_str = "Valid" if res.is_valid else "Has problems"
                    print(f"• {csv_file.name}")
                    print(f"    Columns ({res.column_count}): {', '.join(res.columns[:4])}{'...' if len(res.columns) > 4 else ''}")
                    print(f"    Rows: {res.total_rows} | Delimiter: {repr(res.delimiter)} | Status: {status_str}\n")
                    if not res.is_valid:
                        all_valid = False

            return exit_codes.SUCCESS if all_valid else exit_codes.GENERAL_ERROR
        else:
            # No CSV files in the directory
            print(f"No CSV files found directly in '{args.path}'.")
            print("Tip: Use 'fileguard scan DIRECTORY' to see overall file categories.")
            return exit_codes.SUCCESS

    # Case 3: Target is a non-CSV file
    cat = get_category_for_file(target_path)
    size_kb = target_path.stat().st_size / 1024
    print("File Inspection")
    print(DIVIDER)
    print(f"\nFile:      {args.path}")
    print(f"Category:  {cat}")
    print(f"Size:      {size_kb:.1f} KB")
    print(f"Extension: {target_path.suffix}")
    print("\nNote: Detailed column and row validation is available for .csv files.")
    return exit_codes.SUCCESS
