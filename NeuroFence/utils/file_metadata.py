"""File metadata extraction for uploaded AI models.

Provides a lightweight dataclass and a factory function that reads
filesystem stat information and derives a human-friendly model name.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class FileMetadata:
    """Immutable snapshot of metadata for a single model file."""

    model_name: str        # e.g. "TinyLlama-1.1B"
    filename: str          # e.g. "tinyllama-1.1b.safetensors"
    extension: str         # e.g. ".safetensors"
    size_bytes: int        # raw byte count
    size_display: str      # human-readable — "124.5 MB" or "2.3 GB"
    created_at: datetime
    modified_at: datetime
    filepath: str          # absolute path string


def _humanize_size(size_bytes: int) -> str:
    """Convert bytes to a human-readable string (MB or GB)."""
    gb = size_bytes / (1024 ** 3)
    if gb >= 1.0:
        return f"{gb:.2f} GB"
    mb = size_bytes / (1024 ** 2)
    return f"{mb:.2f} MB"


def _derive_model_name(filename: str) -> str:
    """Derive a readable model name from the raw filename.

    Strips the extension, replaces underscores with hyphens,
    and applies title-case to each segment.

    Example::

        "tinyllama-1.1b.safetensors"  →  "Tinyllama-1.1B"
    """
    stem = Path(filename).stem
    # Replace underscores with hyphens for consistency
    stem = stem.replace("_", "-")
    # Title-case each hyphen-separated segment
    parts = stem.split("-")
    titled = "-".join(part.capitalize() for part in parts)
    return titled


def extract_metadata(filepath: Path | str) -> FileMetadata:
    """Build a :class:`FileMetadata` from the file at *filepath*.

    Args:
        filepath: Absolute path to the model file.

    Returns:
        A populated :class:`FileMetadata` instance.

    Raises:
        FileNotFoundError: If *filepath* does not exist.
    """
    filepath = Path(filepath).resolve()
    stat = os.stat(filepath)

    return FileMetadata(
        model_name=_derive_model_name(filepath.name),
        filename=filepath.name,
        extension=filepath.suffix.lower(),
        size_bytes=stat.st_size,
        size_display=_humanize_size(stat.st_size),
        created_at=datetime.fromtimestamp(stat.st_birthtime if hasattr(stat, "st_birthtime") else stat.st_ctime),
        modified_at=datetime.fromtimestamp(stat.st_mtime),
        filepath=str(filepath),
    )
