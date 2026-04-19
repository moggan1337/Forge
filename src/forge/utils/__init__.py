"""
Utilities for Forge.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from typing import Any


def compute_hash(content: str) -> str:
    """
    Compute a hash of the content.

    Args:
        content: Content to hash

    Returns:
        SHA256 hash of the content
    """
    return hashlib.sha256(content.encode()).hexdigest()


def find_files(directory: str, extensions: list[str]) -> list[Path]:
    """
    Find all files with given extensions in a directory.

    Args:
        directory: Directory to search
        extensions: List of file extensions (e.g., ['.ts', '.tsx'])

    Returns:
        List of matching file paths
    """
    path = Path(directory)
    files = []
    for ext in extensions:
        files.extend(path.rglob(f"*{ext}"))
    return sorted(files)


def create_temp_file(content: str, suffix: str = "") -> Path:
    """
    Create a temporary file with content.

    Args:
        content: Content to write
        suffix: File suffix

    Returns:
        Path to the temporary file
    """
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
    except Exception:
        os.close(fd)
        raise
    return Path(path)


def get_project_root() -> Path:
    """
    Get the project root directory.

    Returns:
        Path to the project root
    """
    return Path(__file__).parent.parent.parent


def ensure_directory(path: Path) -> None:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure exists
    """
    path.mkdir(parents=True, exist_ok=True)


def read_config(config_path: str = "~/.config/forge/config.toml") -> dict[str, Any]:
    """
    Read configuration from a TOML file.

    Args:
        config_path: Path to config file

    Returns:
        Configuration dictionary
    """
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib

    path = Path(config_path).expanduser()
    if not path.exists():
        return {}

    with open(path, "rb") as f:
        return tomllib.load(f)
