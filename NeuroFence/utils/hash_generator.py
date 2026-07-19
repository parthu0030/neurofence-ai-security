"""SHA-256 fingerprint generator for AI model files.

Reads files in fixed-size chunks so that multi-gigabyte models
can be hashed without loading the entire file into memory.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

# 64 KB read buffer — balances speed and memory usage.
_CHUNK_SIZE: int = 65_536


class HashGenerator:
    """Stateless utility for computing cryptographic hashes of files."""

    @staticmethod
    def sha256(filepath: Path | str) -> str:
        """Return the hex-encoded SHA-256 digest for *filepath*.

        Args:
            filepath: Absolute or relative path to the file.

        Returns:
            Lowercase hex string, e.g. ``"4f8d9c0d7d…"``.

        Raises:
            FileNotFoundError: If *filepath* does not exist.
            PermissionError: If the file cannot be read.
        """
        filepath = Path(filepath)
        sha = hashlib.sha256()
        with filepath.open("rb") as fh:
            while chunk := fh.read(_CHUNK_SIZE):
                sha.update(chunk)
        return sha.hexdigest()
