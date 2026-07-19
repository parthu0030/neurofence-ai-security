"""SQLite database manager for NeuroFence AI Security.

Provides a thin wrapper around ``sqlite3`` that manages the
``uploaded_models`` table used by the model upload pipeline.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from config.settings import Paths
from database.models import ModelRecord

# Database lives inside the database/ directory.
_DB_PATH: Path = Paths.DATABASE / "neurofence.db"


class DatabaseManager:
    """Manages the SQLite connection and CRUD operations.

    Usage::

        db = DatabaseManager()
        db.insert_model(record)
        latest = db.get_latest_model()
    """

    def __init__(self, db_path: Path | str | None = None) -> None:
        self._db_path = Path(db_path) if db_path else _DB_PATH
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_tables()

    # ── Connection helper ────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        """Return a new connection with row-factory enabled."""
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    # ── Schema ───────────────────────────────────────────────────────

    def _create_tables(self) -> None:
        """Ensure the ``uploaded_models`` table exists."""
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS uploaded_models (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename    TEXT    NOT NULL UNIQUE,
                    filepath    TEXT    NOT NULL,
                    extension   TEXT    NOT NULL,
                    size        INTEGER NOT NULL,
                    sha256      TEXT    NOT NULL,
                    created_at  TEXT    NOT NULL,
                    modified_at TEXT    NOT NULL,
                    uploaded_at TEXT    NOT NULL
                );
                """
            )

    # ── Write operations ─────────────────────────────────────────────

    def insert_model(self, record: ModelRecord) -> None:
        """Insert or replace a model record keyed on *filename*.

        If a row with the same ``filename`` already exists it is replaced
        so that re-uploads overwrite stale metadata.
        """
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO uploaded_models
                    (filename, filepath, extension, size, sha256,
                     created_at, modified_at, uploaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    record.filename,
                    record.filepath,
                    record.extension,
                    record.size,
                    record.sha256,
                    record.created_at,
                    record.modified_at,
                    record.uploaded_at,
                ),
            )

    # ── Read operations ──────────────────────────────────────────────

    def get_latest_model(self) -> ModelRecord | None:
        """Return the most recently uploaded model, or ``None``."""
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, filename, filepath, extension, size, sha256,
                       created_at, modified_at, uploaded_at
                FROM   uploaded_models
                ORDER  BY uploaded_at DESC
                LIMIT  1;
                """
            ).fetchone()

        if row is None:
            return None

        return ModelRecord(
            id=row["id"],
            filename=row["filename"],
            filepath=row["filepath"],
            extension=row["extension"],
            size=row["size"],
            sha256=row["sha256"],
            created_at=row["created_at"],
            modified_at=row["modified_at"],
            uploaded_at=row["uploaded_at"],
        )
