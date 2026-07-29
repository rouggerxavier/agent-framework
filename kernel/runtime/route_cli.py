"""CLI entry point kept separate from the adaptive policy module."""

from .execution_modes import main


if __name__ == "__main__":
    raise SystemExit(main())
