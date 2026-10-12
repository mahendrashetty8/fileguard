"""Exit codes for FileGuard CLI.

These exit codes allow FileGuard to be safely used in shell scripts,
CI/CD workflows, and automated tasks.
"""

SUCCESS = 0
GENERAL_ERROR = 1
INVALID_ARGUMENT = 2
FILE_NOT_FOUND = 3
PERMISSION_DENIED = 4
OPERATION_FAILED = 5
INTERRUPTED = 130
