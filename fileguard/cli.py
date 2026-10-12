"""Command-Line Interface entry point for FileGuard.

Implements robust argument parsing, subcommand dispatch, and global exception
boundaries to guarantee that no unhandled tracebacks reach the user.
"""

import argparse
import sys
import traceback
from typing import List, Optional

from fileguard import __app_name__, __version__, exit_codes
from fileguard.commands.inspect import execute_inspect
from fileguard.commands.organize import execute_organize
from fileguard.commands.scan import execute_scan
from fileguard.commands.validate import execute_validate
from fileguard.errors import FileGuardError
from fileguard.utils.formatter import format_interrupt
from fileguard.utils.logger import get_logger, set_verbose

# Ensure Windows console supports UTF-8 characters like arrows and box-drawing lines
if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass



CROSS_MARK = "❌"


class FileGuardArgumentParser(argparse.ArgumentParser):
    """Custom ArgumentParser providing clean, friendly error messages without tracebacks."""

    def error(self, message: str) -> None:
        """Handle CLI argument parsing errors gracefully."""
        if "the following arguments are required" in message:
            arg_name = message.split(":")[-1].strip()
            print(f"{CROSS_MARK} Error: Missing required argument: {arg_name}\n", file=sys.stderr)
            print("Please provide all required arguments.", file=sys.stderr)
            print("Run with '--help' to see usage instructions.", file=sys.stderr)
        elif "invalid choice" in message:
            print(f"{CROSS_MARK} Error: Invalid command or option.\n", file=sys.stderr)
            print(f"{message}\n", file=sys.stderr)
            print("Run 'fileguard --help' to see available commands.", file=sys.stderr)
        else:
            print(f"{CROSS_MARK} Error: {message}\n", file=sys.stderr)
            print("Run with '--help' to see usage instructions.", file=sys.stderr)
        sys.exit(exit_codes.INVALID_ARGUMENT)


def build_parser() -> FileGuardArgumentParser:
    """Build and configure the command-line argument parser."""
    parser = FileGuardArgumentParser(
        prog="fileguard",
        description="FileGuard - Safe command-line file organization and validation tool.",
        epilog="Use 'fileguard <command> --help' for more information on a specific command.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"{__app_name__} {__version__}",
        help="Show program's version number and exit",
    )

    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        metavar="{scan,organize,validate}",
    )

    # 1. SCAN subcommand
    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan a directory and display file statistics",
        description="Scan a directory, count files by type, and display category statistics.",
    )
    scan_parser.add_argument(
        "directory",
        help="Directory path to scan",
    )
    scan_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Display detailed diagnostic output during scan",
    )

    # 2. ORGANIZE subcommand
    organize_parser = subparsers.add_parser(
        "organize",
        help="Organize files by file type",
        description="Organize files in the directory into categorized subdirectories.",
    )
    organize_parser.add_argument(
        "directory",
        help="Directory path to organize",
    )
    organize_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying the filesystem",
    )
    organize_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite destination files if they already exist",
    )
    organize_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Display detailed output for each file operation",
    )

    # 3. VALIDATE subcommand
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate a directory before organization",
        description="Check permissions, readability, and conflicts before organizing files.",
    )
    validate_parser.add_argument(
        "directory",
        help="Directory path to validate",
    )
    validate_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Display detailed diagnostic output during validation",
    )

    # 4. INSPECT / INFO subcommand
    inspect_parser = subparsers.add_parser(
        "inspect",
        aliases=["info"],
        help="Inspect a file or directory (supports CSV rows & columns analysis)",
        description="Inspect files or directories, checking CSV columns, rows, delimiter, and integrity.",
    )
    inspect_parser.add_argument(
        "path",
        help="Path to CSV file or directory to inspect",
    )
    inspect_parser.add_argument(
        "--column",
        "--columns",
        "-c",
        nargs="+",
        dest="required_columns",
        metavar="COL",
        help="Verify that the specified column name(s) exist in the CSV file",
    )
    inspect_parser.add_argument(
        "--analyze-columns",
        "--analyze",
        "-a",
        action="store_true",
        dest="analyze_columns",
        help="Analyze and display all column names and data metrics one by one",
    )
    inspect_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Display detailed diagnostic output during inspection",
    )

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Primary execution entry point for FileGuard CLI.

    Args:
        argv: Optional list of argument strings. Uses sys.argv[1:] if None.

    Returns:
        Exit code integer.
    """
    parser = build_parser()

    # Pre-parse check for verbose flag to aid error reporting
    raw_args = argv if argv is not None else sys.argv[1:]
    is_verbose = any(arg in ("-v", "--verbose") for arg in raw_args)
    set_verbose(is_verbose)

    try:
        args = parser.parse_args(argv)

        if not args.command:
            parser.print_help()
            return exit_codes.SUCCESS

        if args.command == "scan":
            return execute_scan(args)
        elif args.command == "organize":
            return execute_organize(args)
        elif args.command == "validate":
            return execute_validate(args)
        elif args.command in ("inspect", "info"):
            return execute_inspect(args)
        else:
            parser.print_help(sys.stderr)
            return exit_codes.INVALID_ARGUMENT

    except KeyboardInterrupt:
        print()
        print(format_interrupt())
        return exit_codes.INTERRUPTED

    except FileGuardError as exc:
        print(exc.format_error(), file=sys.stderr)
        return exc.exit_code

    except SystemExit as exc:
        # Re-raise standard SystemExit (from --help or parser.error)
        return exc.code if isinstance(exc.code, int) else exit_codes.GENERAL_ERROR

    except Exception as exc:
        if is_verbose:
            print("Traceback (most recent call last):", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
        else:
            print(f"{CROSS_MARK} An unexpected error occurred.", file=sys.stderr)
            print("Run with --verbose for additional diagnostic information.", file=sys.stderr)
        return exit_codes.GENERAL_ERROR


if __name__ == "__main__":
    sys.exit(main())
