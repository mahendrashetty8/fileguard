# FileGuard

> **A safe and reliable command-line file organization and validation tool.**

FileGuard is a command-line utility built to demonstrate professional CLI engineering, robust filesystem handling, and fail-safe error management. Rather than merely moving files into folders, FileGuard emphasizes **safety, transparency, and predictability**: operations can be validated beforehand, previewed via dry-run simulation, executed with verbose observability, or stopped cleanly upon user interruption.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture & Design Principles](#architecture--design-principles)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage & Commands](#usage--commands)
  - [`scan`](#1-fileguard-scan)
  - [`organize`](#2-fileguard-organize)
  - [`validate`](#3-fileguard-validate)
- [Execution Modes](#execution-modes)
  - [Dry-Run Mode (`--dry-run`)](#dry-run-mode---dry-run)
  - [Verbose Mode (`--verbose`)](#verbose-mode---verbose)
  - [Force Mode (`--force`)](#force-mode---force)
- [Error Handling Philosophy](#error-handling)
- [Exit Codes](#exit-codes)
- [Project Structure](#project-structure)
- [Automated Testing](#automated-testing)
- [Development & Contribution](#development)
- [Safety & Limitations](#safety--limitations)
- [Future Improvements](#future-improvements)
- [License](#license)

---

## Overview

In day-to-day software development and system administration, file organization scripts often fail catastrophically: unhandled `FileNotFoundError` or `PermissionError` exceptions crash mid-operation, leaving directories in half-modified states; missing flags silently overwrite critical data; and pressing `Ctrl+C` prints ugly stack traces.

**FileGuard solves these issues by treating error handling as a first-class citizen.**

FileGuard classifies files into standardized categories based on file extensions:
- **Images**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.svg`, `.bmp`, `.tiff`, `.ico`
- **Documents**: `.pdf`, `.doc`, `.docx`, `.txt`, `.csv`, `.xlsx`, `.xls`, `.ppt`, `.pptx`, `.rtf`, `.odt`, `.md`
- **Videos**: `.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`, `.flv`, `.webm`, `.m4v`
- **Audio**: `.mp3`, `.wav`, `.aac`, `.flac`, `.ogg`, `.m4a`, `.wma`
- **Archives**: `.zip`, `.rar`, `.7z`, `.tar`, `.gz`, `.bz2`, `.xz`, `.tgz`
- **Other**: Any unrecognized or extensionless file format

---

## Key Features

- **Non-Destructive Scanning**: Inspect folder contents and view breakdown statistics without moving anything.
- **Pre-Flight Validation**: Audit directories for accessibility, unreadable files, and naming conflicts before altering storage.
- **Strict Dry-Run Guarantees**: Preview planned moves without creating folders or touching files on disk.
- **Duplicate Conflict Protection**: Prevents silent overwrites; warns the user and skips conflicts unless `--force` is specified.
- **Atomic & Resilient Moves**: Handles operations cleanly and continues processing batches when non-fatal conflicts occur.
- **Zero Raw Tracebacks**: User-facing exceptions are caught at the application boundary and presented as actionable error messages.
- **Clean Interrupt Handling**: Safely intercepts `Ctrl+C` (`KeyboardInterrupt`), halts processing immediately, and exits with code `130`.
- **Standardized Process Exit Codes**: Fully scriptable for CI/CD and PowerShell/Bash automation.
- **Zero Third-Party Runtime Dependencies**: Built strictly using the Python Standard Library (`pathlib`, `argparse`, `shutil`).

---

## Architecture & Design Principles

FileGuard follows a modular layered architecture:

```
CLI Layer (cli.py, commands/)
           │
           ▼
Service Layer (services/) ──► FileScanner, FileOrganizer, FileValidator
           │
           ▼
Utility Layer (utils/, config.py, errors.py, exit_codes.py)
```

1. **Separation of Concerns**: CLI presentation is completely separated from business logic. Services never call `print()` or `sys.exit()` directly; they return structured dataclasses (`ScanResult`, `OrganizeResult`, `ValidationResult`) or raise domain exceptions.
2. **Explicit Exception Hierarchy**: All internal errors inherit from `FileGuardError`, encapsulating an exit code, target path, and user-facing remediation hint.
3. **Safety First**: Dry-run paths completely bypass filesystem modification logic, making accidental file loss physically impossible.

---

## Requirements

- Python 3.11 or higher
- Windows, macOS, or Linux

---

## Installation

### From Source (Editable / Development Mode)

Clone the repository and install it in editable mode:

```bash
git clone https://github.com/mahendrashetty8/fileguard.git
cd fileguard
pip install -e .
```

### Direct Execution Without Installation

You can run FileGuard directly using Python's module syntax:

```bash
python -m fileguard --help
```

---

## Usage & Commands

```bash
fileguard [-h] [-v] {scan,organize,validate} ...
```

### 1. `fileguard scan`

Scans a directory, counts files, groups them by category, and prints an overview.

```bash
fileguard scan ./Downloads
```

**Example Output:**

```text
FileGuard
────────────────────────────

Scanning: ./Downloads

Files found: 27
Directories: 5

Images:        10
Documents:      8
Videos:         6
Audio:          2
Archives:       1
Other:          0

Scan completed successfully.
```

If the directory contains no files:

```text
No files found.

The directory is empty.

Nothing to organize.
```

---

### 2. `fileguard organize`

Moves files in the target directory into category subfolders (`Images/`, `Documents/`, `Videos/`, `Audio/`, `Archives/`, `Other/`).

```bash
fileguard organize ./Downloads
```

**Options:**
- `--dry-run`: Simulate organization without modifying any files.
- `--force`: Overwrite destination files if duplicates exist.
- `-v, --verbose`: Display detailed operational logs for each action.

**Example Output:**

```text
Organization Summary
────────────────────────────

Total files:    15
Moved files:    14
Skipped files:   1
Failed files:    0

Organization completed successfully.
```

---

### 3. `fileguard validate`

Runs pre-flight verification on a directory prior to organization. It checks:
- Directory existence and permissions
- File readability
- Destination naming conflicts
- Batch case collisions

```bash
fileguard validate ./Downloads
```

**Successful Output:**

```text
Validation
────────────────────────────

Directory: ./Downloads

✓ Directory exists
✓ Directory is accessible
✓ Files can be scanned
✓ No destination conflicts found

Validation successful.
```

**Failure Output (with Problems Detected):**

```text
Validation failed.

Problems found:

1. Destination already exists:
   Images/photo.jpg

2. File cannot be accessed:
   private.pdf

Total problems: 2
```

---

## Execution Modes

### Dry-Run Mode (`--dry-run`)

Simulate organization without creating directories or moving files:

```bash
fileguard organize ./Downloads --dry-run
```

**Output:**

```text
DRY RUN
────────────────────────────

The following changes WOULD be made:

photo.jpg
  → Images/photo.jpg

resume.pdf
  → Documents/resume.pdf

movie.mp4
  → Videos/movie.mp4

No files were changed.
```

---

### Verbose Mode (`--verbose`)

Display real-time logs for diagnosis and traceability:

```bash
fileguard organize ./Downloads --verbose
```

**Output:**

```text
[INFO] Scanning directory
[INFO] Found 15 files
[INFO] Creating Images directory
[INFO] Moving photo.jpg
[INFO] Moving image.png
[INFO] Creating Documents directory
[INFO] Moving resume.pdf

Completed successfully.

Organization Summary
────────────────────────────

Total files:    15
Moved files:    15
Skipped files:   0
Failed files:    0

Organization completed successfully.
```

---

### Force Mode (`--force`)

By default, if `Images/photo.jpg` already exists, FileGuard does not overwrite it:

```text
Warning: destination already exists.

Source:
photo.jpg

Destination:
Images/photo.jpg

Skipping file.

Use --force if you want to replace the destination.
```

When `--force` is supplied, FileGuard replaces the destination file safely using atomic operations:

```bash
fileguard organize ./Downloads --force
```

---

## Error Handling

FileGuard is designed to fail gracefully.

Expected errors are converted into human-readable messages instead of raw Python tracebacks.

Examples include:

- Missing directories
- Invalid paths
- Permission errors
- Duplicate destinations
- Invalid arguments
- File operation failures
- User interruption

The application also uses meaningful process exit codes so it can be safely used in scripts and automation.

### Examples of Graceful Error Outputs

#### Missing Directory

```bash
fileguard scan missing-folder
```

```text
Error: Directory not found.

Path:
missing-folder

Please check that the directory exists.
```

#### File Provided Instead of Directory

```bash
fileguard organize resume.pdf
```

```text
Error: Expected a directory.

'resume.pdf' is a file.

Please provide a directory path.
```

#### Permission Denied

```text
Error: Permission denied.

FileGuard cannot access:

./protected

Check your permissions and try again.
```

#### User Interruption (`Ctrl+C`)

Pressing `Ctrl+C` halts processing safely without printing a stack trace:

```text
^C

Operation interrupted by user.

FileGuard stopped safely.
No further files will be processed.
```

---

## Exit Codes

FileGuard returns deterministic process exit codes for integration into shell scripts and CI pipelines:

| Code | Meaning | Description |
|:---:|:---|:---|
| **0** | `SUCCESS` | Operation completed successfully |
| **1** | `GENERAL_ERROR` | General or unexpected application error / validation problem |
| **2** | `INVALID_ARGUMENT` | Missing/invalid arguments or file provided where directory expected |
| **3** | `FILE_NOT_FOUND` | Target directory does not exist |
| **4** | `PERMISSION_DENIED` | Filesystem access or read/write permission denied |
| **5** | `OPERATION_FAILED` | File move or category folder creation failure |
| **130** | `INTERRUPTED` | User halted process with `Ctrl+C` |

---

## Project Structure

```text
fileguard/
│
├── fileguard/
│   ├── __init__.py           # Package version and metadata
│   ├── __main__.py           # Entry point for python -m fileguard
│   ├── cli.py                # Argument parsing and global error boundaries
│   ├── errors.py             # Domain exception hierarchy
│   ├── exit_codes.py         # Standardized exit code constants
│   ├── config.py             # Category extensions and mapping rules
│   │
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── organize.py       # Organize command controller
│   │   ├── scan.py           # Scan command controller
│   │   └── validate.py       # Validate command controller
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── file_scanner.py   # Pure discovery and category counting
│   │   ├── file_organizer.py # Directory creation, move, conflict logic
│   │   └── file_validator.py # Pre-flight validation inspection
│   │
│   └── utils/
│       ├── __init__.py
│       ├── formatter.py      # Terminal presentation formatting
│       ├── filesystem.py     # Reusable filesystem guards and safe operations
│       └── logger.py         # Verbose logging handler
│
├── tests/
│   ├── __init__.py
│   ├── test_cli.py           # CLI argument parsing and dispatch tests
│   ├── test_errors.py        # Exception hierarchy and exit code tests
│   ├── test_interrupt.py     # Ctrl+C signal handling tests
│   ├── test_organizer.py     # File organizer service tests
│   ├── test_scanner.py       # File scanner service tests
│   └── test_validator.py     # File validator service tests
│
├── examples/
│   └── demo/                 # Live demonstration directory
│       ├── Documents/
│       ├── Images/
│       └── sample files
│
├── .gitignore                # Standard Python Git ignore patterns
├── LICENSE                   # MIT License
├── README.md                 # Complete documentation
├── pyproject.toml            # Modern PEP 517/621 packaging configuration
└── requirements.txt          # Minimal development dependencies
```

---

## Automated Testing

FileGuard includes a test suite covering both happy and unhappy paths across the application.

Run the test suite with `pytest`:

```bash
pytest
```

Run with verbose test reporting:

```bash
pytest -v
```

### Test Coverage Highlights:
- **CLI Options**: `--help`, `scan --help`, `organize --help`, `validate --help`, `--version`, missing arguments, invalid commands.
- **Scanner Service**: Populated folders, missing paths, file-as-directory handling, empty directories, extension categorization, uppercase extensions.
- **Organizer Service**: Normal moves, dry-run immutability, duplicate skipping, `--force` replacement, unknown extension routing, error resilience.
- **Validator Service**: Clean directories, missing directories, destination conflicts, unreadable file detection.
- **Error Formatting**: Exact terminal message checks for missing paths, files-as-directories, permission denial.
- **Signal Interruption**: Interception of `KeyboardInterrupt` verifying exit code `130` and clean terminal output without tracebacks.

---

## Development

To set up a local development environment:

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .venv\Scripts\Activate.ps1
   # Linux / macOS:
   source .venv/bin/activate
   ```
2. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```
3. Run tests before submitting changes:
   ```bash
   pytest
   ```

---

## Safety & Limitations

- **Top-Level Organization**: FileGuard organizes files directly located in the target directory into designated subdirectories. It does not blindly recurse into child directories, protecting nested folder structures from destruction.
- **Non-Destructive Dry-Run**: The dry-run code path avoids modifying the filesystem.
- **Atomic Operations**: On supported operating systems, file replacements with `--force` utilize atomic replacements (`os.replace`).
- **No Command Execution**: FileGuard never executes file contents or shell scripts found in scanned directories.

---

## Future Improvements

- Support for user-defined configuration files (e.g. `.fileguard.json` or `pyproject.toml` tool sections) for custom extension mappings.
- Optional recursive organization mode with depth limits (`--recursive`, `--max-depth`).
- Undo log / rollback ledger for reversing organization operations.
- Parallel file operations for high-latency network shares.

---

## License

This project is licensed under the [MIT License](LICENSE).
