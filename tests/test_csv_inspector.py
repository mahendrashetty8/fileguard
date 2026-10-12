"""Tests for CSV Inspector service and CLI inspect/info command."""

from pathlib import Path
import pytest

from fileguard import exit_codes
from fileguard.cli import main
from fileguard.errors import DirectoryNotFoundError
from fileguard.services.csv_inspector import CSVInspector


def test_csv_inspector_valid_file(tmp_path: Path):
    """Verify inspection of a standard comma-separated CSV file."""
    csv_file = tmp_path / "data.csv"
    csv_file.write_text(
        "id,name,age,city\n"
        "1,Alice,25,Seattle\n"
        "2,Bob,30,New York\n"
        "3,Charlie,35,Chicago\n",
        encoding="utf-8",
    )

    inspector = CSVInspector()
    result = inspector.inspect(csv_file)

    assert result.is_valid is True
    assert result.column_count == 4
    assert result.columns == ["id", "name", "age", "city"]
    assert result.total_rows == 3
    assert result.delimiter == ","
    assert result.encoding == "utf-8"
    assert len(result.problems) == 0


def test_csv_inspector_detects_ragged_rows(tmp_path: Path):
    """Verify inspection identifies rows with mismatched column counts."""
    csv_file = tmp_path / "ragged.csv"
    csv_file.write_text(
        "col1,col2,col3\n"
        "val1,val2,val3\n"
        "bad_row_only_two_values,val2\n",
        encoding="utf-8",
    )

    inspector = CSVInspector()
    result = inspector.inspect(csv_file)

    assert result.is_valid is False
    assert result.column_count == 3
    assert result.total_rows == 2
    assert len(result.problems) >= 1
    assert any("Row 3 has 2 columns (expected 3)" in p for p in result.problems)


def test_csv_inspector_semicolon_delimiter(tmp_path: Path):
    """Verify detection of semicolon-delimited CSV files."""
    csv_file = tmp_path / "semicolon.csv"
    csv_file.write_text(
        "A;B;C\n"
        "1;2;3\n"
        "4;5;6\n",
        encoding="utf-8",
    )

    inspector = CSVInspector()
    result = inspector.inspect(csv_file)

    assert result.is_valid is True
    assert result.column_count == 3
    assert result.delimiter == ";"
    assert result.total_rows == 2


def test_csv_inspector_empty_file(tmp_path: Path):
    """Verify inspection of an empty CSV file."""
    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("", encoding="utf-8")

    inspector = CSVInspector()
    result = inspector.inspect(empty_file)

    assert result.is_valid is True
    assert result.total_rows == 0
    assert result.column_count == 0


def test_csv_inspector_missing_file_raises_error(tmp_path: Path):
    """Verify inspecting non-existent file raises DirectoryNotFoundError."""
    missing = tmp_path / "missing.csv"
    inspector = CSVInspector()

    with pytest.raises(DirectoryNotFoundError):
        inspector.inspect(missing)


def test_cli_inspect_command(tmp_path: Path, capsys):
    """Verify running 'fileguard inspect <file>' through CLI prints CSV summary."""
    csv_file = tmp_path / "students.csv"
    csv_file.write_text("id,name,score\n101,John,95\n102,Jane,98\n", encoding="utf-8")

    exit_code = main(["inspect", str(csv_file)])
    assert exit_code == exit_codes.SUCCESS

    captured = capsys.readouterr()
    assert "CSV Inspection" in captured.out
    assert "Columns (3):" in captured.out
    assert "Total rows:  2" in captured.out
    assert "Delimiter:   ','" in captured.out
    assert "Valid" in captured.out


def test_cli_info_alias_command(tmp_path: Path, capsys):
    """Verify running 'fileguard info <file>' through CLI alias prints CSV summary."""
    csv_file = tmp_path / "grades.csv"
    csv_file.write_text("course,grade\nMath,A\nEnglish,B\n", encoding="utf-8")

    exit_code = main(["info", str(csv_file)])
    assert exit_code == exit_codes.SUCCESS

    captured = capsys.readouterr()
    assert "CSV Inspection" in captured.out
    assert "Columns (2):" in captured.out
    assert "Total rows:  2" in captured.out


def test_csv_inspector_required_column_missing(tmp_path: Path):
    """Verify checking non-existent required columns flags missing columns."""
    csv_file = tmp_path / "check.csv"
    csv_file.write_text("id,name\n1,Alice\n", encoding="utf-8")

    inspector = CSVInspector()
    result = inspector.inspect(csv_file, required_columns=["id", "email"])

    assert result.is_valid is False
    assert "email" in result.missing_columns
    assert "id" not in result.missing_columns
    assert any("Required column 'email' is not present" in p for p in result.problems)


def test_csv_inspector_column_by_column_analysis(tmp_path: Path):
    """Verify column-by-column analysis infers types and metrics correctly."""
    csv_file = tmp_path / "data.csv"
    csv_file.write_text(
        "age,score,city,active\n"
        "20,88.5,Boston,True\n"
        "22,91.0,Seattle,False\n"
        "19,,Boston,True\n",
        encoding="utf-8",
    )

    inspector = CSVInspector()
    result = inspector.inspect(csv_file, analyze_columns=True)

    assert len(result.column_analyses) == 4

    # 1. Age: Integer
    age_col = result.column_analyses[0]
    assert age_col.name == "age"
    assert age_col.inferred_type == "Integer"
    assert age_col.min_value == "19"
    assert age_col.max_value == "22"
    assert age_col.missing_count == 0

    # 2. Score: Decimal with 1 missing
    score_col = result.column_analyses[1]
    assert score_col.name == "score"
    assert score_col.inferred_type == "Decimal"
    assert score_col.missing_count == 1
    assert score_col.populated_count == 2

    # 3. City: Text
    city_col = result.column_analyses[2]
    assert city_col.name == "city"
    assert city_col.inferred_type == "Text"
    assert city_col.unique_count == 2


def test_cli_missing_column_error(tmp_path: Path, capsys):
    """Verify CLI returns error and lists missing columns when --column is not found."""
    csv_file = tmp_path / "members.csv"
    csv_file.write_text("name,role\nAlice,Admin\nBob,User\n", encoding="utf-8")

    exit_code = main(["inspect", str(csv_file), "--column", "email", "phone"])
    assert exit_code == exit_codes.INVALID_ARGUMENT

    captured = capsys.readouterr()
    assert "Error: Required column(s) not found in CSV file." in captured.out
    assert "• email" in captured.out
    assert "• phone" in captured.out
    assert "Available columns in file (2):" in captured.out
    assert "1. name" in captured.out
    assert "2. role" in captured.out


def test_cli_analyze_columns_output(tmp_path: Path, capsys):
    """Verify CLI --analyze-columns displays all columns one by one."""
    csv_file = tmp_path / "stats.csv"
    csv_file.write_text("user_id,points\nU01,50\nU02,75\n", encoding="utf-8")

    exit_code = main(["inspect", str(csv_file), "--analyze-columns"])
    assert exit_code == exit_codes.SUCCESS

    captured = capsys.readouterr()
    assert "Column-by-Column Analysis" in captured.out
    assert "[1/2] Column: user_id" in captured.out
    assert "[2/2] Column: points" in captured.out
    assert "Type:" in captured.out
    assert "Populated:" in captured.out
    assert "Samples:" in captured.out

