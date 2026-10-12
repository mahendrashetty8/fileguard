"""Output formatter for FileGuard CLI.

Centralizes CLI output formatting across all commands to ensure a clean,
consistent, and professional terminal appearance on Windows, macOS, and Linux.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _can_encode(text: str) -> bool:
    """Check if the current stdout stream can encode the given string."""
    try:
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        text.encode(encoding)
        return True
    except Exception:
        return False


DIVIDER = "────────────────────────────" if _can_encode("─") else "----------------------------"
ARROW = "→" if _can_encode("→") else "->"
CHECK_MARK = "✓" if _can_encode("✓") else "[OK]"
CROSS_MARK = "❌"


def format_header(title: str) -> str:
    """Format a section header with standard divider."""
    return f"{title}\n{DIVIDER}"


def format_success(message: str) -> str:
    """Format a success message."""
    return f"{message}"


def format_warning(message: str) -> str:
    """Format a warning message."""
    return f"Warning: {message}"


def format_error(message: str) -> str:
    """Format an error message with ❌ symbol."""
    return f"{CROSS_MARK} Error: {message}"


def format_empty_directory(action: str = "organize") -> str:
    """Format the message for an empty directory."""
    return (
        "No files found.\n\n"
        "The directory is empty.\n\n"
        f"Nothing to {action}."
    )


def format_interrupt() -> str:
    """Format the message shown when interrupted by Ctrl+C."""
    return (
        "^C\n\n"
        "Operation interrupted by user.\n\n"
        "FileGuard stopped safely.\n"
        "No further files will be processed."
    )


def format_duplicate_warning(
    source_name: str,
    destination_rel_path: str,
) -> str:
    """Format warning when destination already exists without --force."""
    return (
        "Warning: destination already exists.\n\n"
        f"Source:\n{source_name}\n\n"
        f"Destination:\n{destination_rel_path}\n\n"
        "Skipping file.\n\n"
        "Use --force if you want to replace the destination."
    )


def format_scan_result(
    directory: str,
    files_found: int,
    directories_found: int,
    category_counts: Dict[str, int],
) -> str:
    """Format the statistics output for the scan command."""
    lines = [
        "FileGuard",
        DIVIDER,
        "",
        f"Scanning: {directory}",
        "",
        f"Files found: {files_found}",
        f"Directories: {directories_found}",
        "",
    ]

    for category, count in category_counts.items():
        # Pad category to 12 chars for aligned output
        lines.append(f"{category + ':':<14} {count}")

    lines.extend(["", "Scan completed successfully."])
    return "\n".join(lines)


def format_dry_run_header() -> str:
    """Format dry run header."""
    return (
        "DRY RUN\n"
        f"{DIVIDER}\n\n"
        "The following changes WOULD be made:"
    )


def format_dry_run_entry(source_name: str, destination_display: str) -> str:
    """Format a single dry run change preview entry."""
    return f"{source_name}\n  {ARROW} {destination_display}"


def format_organize_summary(
    total_files: int,
    moved_files: int,
    skipped_files: int,
    failed_files: int,
    is_dry_run: bool = False,
) -> str:
    """Format summary at the conclusion of organize operation."""
    if is_dry_run:
        return "\nNo files were changed."

    lines = [
        "",
        "Organization Summary",
        DIVIDER,
        "",
        f"Total files:    {total_files}",
        f"Moved files:    {moved_files}",
        f"Skipped files:  {skipped_files}",
        f"Failed files:   {failed_files}",
        "",
    ]
    if failed_files > 0:
        lines.append("Organization completed with errors.")
    else:
        lines.append("Organization completed successfully.")
    return "\n".join(lines)


def format_validation_success(
    directory: str,
    checks: List[str],
) -> str:
    """Format successful validation output."""
    lines = [
        "Validation",
        DIVIDER,
        "",
        f"Directory: {directory}",
        "",
    ]
    for check in checks:
        lines.append(f"{CHECK_MARK} {check}")
    lines.extend(["", "Validation successful."])
    return "\n".join(lines)


def format_validation_failure(
    directory: str,
    problems: List[str],
) -> str:
    """Format failed validation output with numbered problem list."""
    lines = [
        f"{CROSS_MARK} Validation failed.",
        "",
        "Problems found:",
        "",
    ]
    for idx, problem in enumerate(problems, start=1):
        lines.append(f"{idx}. {problem}")
        lines.append("")

    lines.append(f"Total problems: {len(problems)}")
    return "\n".join(lines)


def format_csv_inspection(
    file_path: str,
    columns: List[str],
    total_rows: int,
    delimiter: str,
    encoding: str,
    is_valid: bool,
    problems: List[str],
) -> str:
    """Format structured CSV inspection report."""
    delim_repr = repr(delimiter)
    col_count = len(columns)

    lines = [
        "CSV Inspection",
        DIVIDER,
        "",
        f"File: {file_path}",
        "",
        f"Columns ({col_count}):",
    ]

    # Align column numbers neatly
    max_num_width = len(str(col_count))
    for idx, col in enumerate(columns, start=1):
        num_str = f"{idx}.".rjust(max_num_width + 1)
        lines.append(f"  {num_str} {col}")

    lines.extend([
        "",
        f"Total rows:  {total_rows}",
        f"Delimiter:   {delim_repr}",
        f"Encoding:    {encoding}",
    ])

    if is_valid:
        lines.append(f"Status:      Valid (all rows have consistent {col_count} columns)")
    else:
        lines.append("Status:      Invalid")
        lines.append("")
        lines.append("Problems found:")
        for idx, problem in enumerate(problems, start=1):
            lines.append(f"{idx}. {problem}")

    return "\n".join(lines)


def format_missing_columns_error(
    file_path: str,
    missing_columns: List[str],
    available_columns: List[str],
) -> str:
    """Format user-friendly error when requested columns are not present in CSV."""
    lines = [
        f"{CROSS_MARK} Error: Required column(s) not found in CSV file.",
        "",
        f"File:\n{file_path}",
        "",
        "Missing column(s):",
    ]
    for col in missing_columns:
        lines.append(f"  • {col}")

    lines.extend([
        "",
        f"Available columns in file ({len(available_columns)}):",
    ])
    max_num_width = len(str(len(available_columns)))
    for idx, col in enumerate(available_columns, start=1):
        num_str = f"{idx}.".rjust(max_num_width + 1)
        lines.append(f"  {num_str} {col}")

    lines.extend(["", "Please check column spelling and try again."])
    return "\n".join(lines)


def format_column_analysis(
    file_path: str,
    total_rows: int,
    total_cols: int,
    analyses: List[Any],
) -> str:
    """Format detailed column-by-column analysis report."""
    lines = [
        "Column-by-Column Analysis",
        DIVIDER,
        "",
        f"File: {file_path}",
        f"Dimensions: {total_rows} row(s) x {total_cols} column(s)",
        "",
    ]
    for a in analyses:
        pct = (a.populated_count / total_rows * 100) if total_rows > 0 else 0.0
        lines.append(f"[{a.index}/{total_cols}] Column: {a.name}")
        lines.append(f"  Type:         {a.inferred_type}")
        lines.append(f"  Populated:    {a.populated_count}/{total_rows} ({pct:.1f}%)")
        lines.append(f"  Missing:      {a.missing_count}")
        lines.append(f"  Unique:       {a.unique_count}")
        if a.min_value is not None and a.max_value is not None and a.inferred_type in ("Integer", "Decimal"):
            lines.append(f"  Range:        {a.min_value} to {a.max_value}")
        if a.sample_values:
            sample_preview = ", ".join(repr(s) if "," in s else s for s in a.sample_values)
            lines.append(f"  Samples:      {sample_preview}")
        lines.append("")
    return "\n".join(lines).rstrip()


