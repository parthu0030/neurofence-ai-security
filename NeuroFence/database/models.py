"""Data-transfer objects for database records.

Each dataclass mirrors a single database table and serves as the
canonical shape for data flowing between the service layer and the UI.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ModelRecord:
    """Represents a row in the ``uploaded_models`` table.

    Attributes:
        id:          Auto-incremented primary key (``None`` before insertion).
        filename:    Original file name, e.g. ``"tinyllama-1.1b.safetensors"``.
        filepath:    Absolute path to the file inside ``uploads/``.
        extension:   Lowercase extension, e.g. ``".safetensors"``.
        size:        File size in bytes.
        sha256:      Hex-encoded SHA-256 fingerprint.
        created_at:  File creation timestamp.
        modified_at: File last-modified timestamp.
        uploaded_at: Timestamp of the upload event.
    """

    filename: str
    filepath: str
    extension: str
    size: int
    sha256: str
    created_at: str
    modified_at: str
    uploaded_at: str
    id: int | None = None
