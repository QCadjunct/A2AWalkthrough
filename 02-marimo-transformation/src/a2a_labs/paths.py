"""Shared path resolution for the repository.

The ``data/`` folder lives at the repository root and is shared by all three
sections (A2A original, Marimo transformation, three-tier). Code should never
hardcode a relative path like ``"data/doctors.json"`` — that breaks the moment a
notebook runs from a subdirectory. Instead, resolve from here.

``DATA_DIR`` is found by walking up from this file until a directory containing
``data/`` is located, so it works regardless of the caller's working directory.
"""

from __future__ import annotations

from pathlib import Path


def _find_repo_root(start: Path) -> Path:
    """Walk upward until a directory containing ``data/`` is found.

    Falls back to three levels up (the repo root relative to
    ``<root>/02-marimo-transformation/src/a2a_labs/paths.py``) if no marker is
    found, so the constant is always defined.
    """
    for parent in [start, *start.parents]:
        if (parent / "data").is_dir():
            return parent
    return start.parents[3] if len(start.parents) > 3 else start


REPO_ROOT: Path = _find_repo_root(Path(__file__).resolve())
DATA_DIR: Path = REPO_ROOT / "data"


def data_path(*parts: str) -> Path:
    """Return an absolute path inside the shared ``data/`` folder.

    Example: ``data_path("doctors.json")`` ->
    ``<repo>/data/doctors.json`` no matter where the caller runs from.
    """
    return DATA_DIR.joinpath(*parts)
