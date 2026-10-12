"""Custom exceptions for FileGuard.

This module defines the hierarchy of domain exceptions used throughout FileGuard.
Every exception includes a corresponding exit code and provides structured details
for generating human-friendly error messages instead of raw Python tracebacks.
"""

from typing import Optional
from fileguard import exit_codes

CROSS_MARK = "❌"


class FileGuardError(Exception):
    """Base exception for all FileGuard errors.

    Attributes:
        message: Human-readable error description.
        exit_code: Process exit code associated with this error.
        path: Optional filesystem path related to the error.
        hint: Optional guidance on how the user can resolve the issue.
    """

    def __init__(
        self,
        message: str,
        exit_code: int = exit_codes.GENERAL_ERROR,
        path: Optional[str] = None,
        hint: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code
        self.path = path
        self.hint = hint

    def format_error(self) -> str:
        """Format the error message for terminal presentation."""
        lines = [f"{CROSS_MARK} Error: {self.message}"]
        if self.path:
            lines.extend(["", "Path:", str(self.path)])
        if self.hint:
            lines.extend(["", self.hint])
        return "\n".join(lines)


class DirectoryNotFoundError(FileGuardError):
    """Raised when a specified directory does not exist."""

    def __init__(
        self,
        message: str = "Directory not found.",
        path: Optional[str] = None,
        hint: Optional[str] = "Please check that the directory exists.",
    ) -> None:
        super().__init__(
            message=message,
            exit_code=exit_codes.FILE_NOT_FOUND,
            path=path,
            hint=hint,
        )


class InvalidInputError(FileGuardError):
    """Raised when an argument or path is invalid (e.g., file provided where directory expected)."""

    def __init__(
        self,
        message: str = "Expected a directory.",
        path: Optional[str] = None,
        hint: Optional[str] = "Please provide a directory path.",
    ) -> None:
        super().__init__(
            message=message,
            exit_code=exit_codes.INVALID_ARGUMENT,
            path=path,
            hint=hint,
        )

    def format_error(self) -> str:
        """Format expected directory error matching specification."""
        if self.path and "is a file" not in self.message:
            lines = [
                f"{CROSS_MARK} Error: {self.message}",
                "",
                f"'{self.path}' is a file.",
            ]
            if self.hint:
                lines.extend(["", self.hint])
            return "\n".join(lines)
        return super().format_error()


class PermissionDeniedError(FileGuardError):
    """Raised when filesystem access is denied."""

    def __init__(
        self,
        message: str = "Permission denied.",
        path: Optional[str] = None,
        hint: Optional[str] = "Check your permissions and try again.",
    ) -> None:
        super().__init__(
            message=message,
            exit_code=exit_codes.PERMISSION_DENIED,
            path=path,
            hint=hint,
        )

    def format_error(self) -> str:
        """Format permission denied error matching specification."""
        lines = [f"{CROSS_MARK} Error: {self.message}"]
        if self.path:
            lines.extend(["", "FileGuard cannot access:", "", str(self.path)])
        if self.hint:
            lines.extend(["", self.hint])
        return "\n".join(lines)


class FileOperationError(FileGuardError):
    """Raised when a filesystem operation (e.g. moving or creating) fails."""

    def __init__(
        self,
        message: str = "File operation failed.",
        path: Optional[str] = None,
        hint: Optional[str] = "Check file permissions and ensure target destination is writable.",
    ) -> None:
        super().__init__(
            message=message,
            exit_code=exit_codes.OPERATION_FAILED,
            path=path,
            hint=hint,
        )
