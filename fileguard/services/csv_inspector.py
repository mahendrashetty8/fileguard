"""CSV Inspector and Validator service for FileGuard.

Inspects CSV files for structure, header integrity, row/column counts,
delimiters, column existence verification, and column-by-column data profiling.
"""

import csv
from dataclasses import dataclass, field
import io
from pathlib import Path
from typing import List, Optional, Tuple, Union

from fileguard.errors import DirectoryNotFoundError, InvalidInputError, PermissionDeniedError


@dataclass
class ColumnAnalysis:
    """Detailed profile metrics for an individual CSV column."""

    index: int
    name: str
    inferred_type: str  # "Integer", "Decimal", "Text", "Empty"
    total_count: int
    populated_count: int
    missing_count: int
    unique_count: int
    sample_values: List[str]
    min_value: Optional[str] = None
    max_value: Optional[str] = None


@dataclass
class CSVInspectionResult:
    """Detailed structural results from inspecting a CSV file."""

    path: Path
    is_valid: bool = True
    total_rows: int = 0
    column_count: int = 0
    columns: List[str] = field(default_factory=list)
    delimiter: str = ","
    encoding: str = "utf-8"
    problems: List[str] = field(default_factory=list)
    preview_rows: List[List[str]] = field(default_factory=list)
    missing_columns: List[str] = field(default_factory=list)
    column_analyses: List[ColumnAnalysis] = field(default_factory=list)

    @property
    def has_header(self) -> bool:
        """True if columns list contains header names."""
        return len(self.columns) > 0


class CSVInspector:
    """Inspects, verifies column existence, and profiles data in CSV files."""

    SUPPORTED_ENCODINGS = ("utf-8", "utf-8-sig", "latin-1", "cp1252")

    def inspect(
        self,
        file_path: Union[Path, str],
        required_columns: Optional[List[str]] = None,
        analyze_columns: bool = False,
    ) -> CSVInspectionResult:
        """Inspect a CSV file, check required columns, and optionally analyze each column.

        Args:
            file_path: Path to target CSV file.
            required_columns: List of column names that must be present in the file.
            analyze_columns: If True, profile all columns one by one.

        Returns:
            CSVInspectionResult with column names, row counts, and error reports.

        Raises:
            DirectoryNotFoundError: If file does not exist.
            PermissionDeniedError: If file cannot be read.
            InvalidInputError: If path is a directory instead of a file.
        """
        path = Path(file_path)

        if not path.exists():
            raise DirectoryNotFoundError(
                message="File not found.",
                path=str(path),
                hint="Please check that the file path is correct.",
            )

        if path.is_dir():
            raise InvalidInputError(
                message="Expected a CSV file, but received a directory.",
                path=str(path),
                hint="Pass a CSV file to inspect its rows and columns.",
            )

        result = CSVInspectionResult(path=path)

        # Detect readable encoding
        content: Optional[str] = None
        for enc in self.SUPPORTED_ENCODINGS:
            try:
                with open(path, mode="r", encoding=enc) as f:
                    content = f.read()
                result.encoding = enc
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
            except PermissionError as exc:
                raise PermissionDeniedError(
                    message="Permission denied reading CSV file.",
                    path=str(path),
                ) from exc

        if content is None:
            result.is_valid = False
            result.problems.append("Unable to decode file using standard text encodings.")
            return result

        if not content.strip():
            result.is_valid = True
            result.total_rows = 0
            result.column_count = 0
            if required_columns:
                result.is_valid = False
                result.missing_columns = list(required_columns)
                for col in required_columns:
                    result.problems.append(f"Required column '{col}' not present (file is empty).")
            return result

        # Detect delimiter
        delimiter = self._detect_delimiter(content)
        result.delimiter = delimiter

        # Parse rows
        try:
            reader = csv.reader(io.StringIO(content), delimiter=delimiter)
            all_rows: List[List[str]] = []
            for row in reader:
                if row or all_rows:
                    all_rows.append(row)
        except csv.Error as exc:
            result.is_valid = False
            result.problems.append(f"CSV parsing error: {exc}")
            return result

        if not all_rows:
            result.is_valid = True
            return result

        # First row is header
        header = [col.strip() for col in all_rows[0]]
        expected_cols = len(header)
        result.columns = header
        result.column_count = expected_cols

        data_rows = all_rows[1:]
        result.total_rows = len(data_rows)
        result.preview_rows = data_rows[:5]

        # 1. Verify required column names
        if required_columns:
            header_map = {col.lower(): col for col in header}
            for req in required_columns:
                # Check exact match first, then case-insensitive
                if req not in header and req.lower() not in header_map:
                    result.missing_columns.append(req)
                    result.problems.append(f"Required column '{req}' is not present in the CSV file.")

        # 2. Validate column consistency across all rows
        ragged_errors = 0
        for row_idx, row in enumerate(data_rows, start=2):
            if len(row) != expected_cols:
                ragged_errors += 1
                if ragged_errors <= 5:
                    result.problems.append(
                        f"Row {row_idx} has {len(row)} columns (expected {expected_cols})"
                    )

        if ragged_errors > 5:
            result.problems.append(f"... and {ragged_errors - 5} more rows with mismatched column counts.")

        # 3. Analyze each column one by one if requested
        if analyze_columns and result.columns:
            for idx, col_name in enumerate(result.columns, start=1):
                col_values = [row[idx - 1] if len(row) >= idx else "" for row in data_rows]
                analysis = self._analyze_single_column(idx, col_name, col_values)
                result.column_analyses.append(analysis)

        result.is_valid = len(result.problems) == 0
        return result

    def _analyze_single_column(self, col_idx: int, col_name: str, values: List[str]) -> ColumnAnalysis:
        """Profile and analyze a single column's data values."""
        total = len(values)
        non_empty = [v.strip() for v in values if v is not None and v.strip() != ""]
        empty_count = total - len(non_empty)

        # Inferred type check
        inferred_type = "Text"
        min_val = None
        max_val = None

        if not non_empty:
            inferred_type = "Empty"
        else:
            is_int = True
            is_float = True
            int_vals = []
            float_vals = []

            for v in non_empty:
                if is_int:
                    try:
                        int_vals.append(int(v))
                    except ValueError:
                        is_int = False
                if is_float:
                    try:
                        float_vals.append(float(v))
                    except ValueError:
                        is_float = False

            if is_int:
                inferred_type = "Integer"
                min_val = str(min(int_vals))
                max_val = str(max(int_vals))
            elif is_float:
                inferred_type = "Decimal"
                min_val = str(min(float_vals))
                max_val = str(max(float_vals))
            elif all(v.lower() in ("true", "false", "yes", "no", "0", "1") for v in non_empty):
                inferred_type = "Boolean"

        # Unique values and samples
        unique_vals = list(dict.fromkeys(non_empty))
        samples = unique_vals[:4]

        return ColumnAnalysis(
            index=col_idx,
            name=col_name,
            inferred_type=inferred_type,
            total_count=total,
            populated_count=len(non_empty),
            missing_count=empty_count,
            unique_count=len(unique_vals),
            sample_values=samples,
            min_value=min_val,
            max_value=max_val,
        )

    def _detect_delimiter(self, sample_text: str) -> str:
        """Heuristically identify the CSV delimiter character."""
        first_line = sample_text.splitlines()[0] if sample_text.splitlines() else ""
        candidates = [",", ";", "\t", "|"]
        counts = {cand: first_line.count(cand) for cand in candidates}
        best_cand = max(counts, key=lambda c: counts[c])
        return best_cand if counts[best_cand] > 0 else ","
