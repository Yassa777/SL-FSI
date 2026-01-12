"""Resolve repository paths for SL-FSI."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable


def _candidate_markers() -> Iterable[str]:
    return ("pyproject.toml", ".git")


def find_repo_root(start: Path | None = None) -> Path:
    """Locate the repository root by walking upward.

    Args:
        start: Starting path to search from. Defaults to the current working directory.

    Returns:
        The first parent directory containing a marker file.
    """
    current = (start or Path.cwd()).resolve()
    for parent in (current, *current.parents):
        for marker in _candidate_markers():
            if (parent / marker).exists():
                return parent
    return current
