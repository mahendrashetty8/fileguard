"""Executable module entry point for python -m fileguard."""

import sys
from fileguard.cli import main

if __name__ == "__main__":
    sys.exit(main())
