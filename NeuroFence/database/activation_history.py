"""Activation history repository for NeuroFence.

Encapsulates all SQLite operations for the ``activation_history`` table.
Separated from :mod:`database.database` to keep the main manager lean.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from database.models import ActivationHistoryRecord


class ActivationHistoryRepository:
    """CRUD operations for the ``activation_history`` table.

    This class does **not** own a connection pool — it receives the
    database path and creates short-lived connections per operation,
    matching the pattern in :class:`database.database.DatabaseManager`.

    Usage::

        repo = ActivationHistoryRepository(db_path)
        repo.insert_batch(prompt_id, records)
        rows = repo.get_by_prompt(prompt_id)
    """

    def __init__(self, db_path: Path | str) -> None:
        self._db_path = str(db_path)

    # ── Connection helper ────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ── Write operations ─────────────────────────────────────────────

    def insert_batch(
        self,
        records: list[ActivationHistoryRecord],
    ) -> None:
        """Bulk-insert all layer summaries for a single prompt execution.

        Args:
            records: List of :class:`ActivationHistoryRecord` objects,
                     one per captured layer.
        """
        if not records:
            return

        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO activation_history
                    (prompt_id, layer_number, mean, std, minimum,
                     maximum, norm, tensor_shape, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                [
                    (
                        r.prompt_id,
                        r.layer_number,
                        r.mean,
                        r.std,
                        r.minimum,
                        r.maximum,
                        r.norm,
                        r.tensor_shape,
                        r.created_at,
                    )
                    for r in records
                ],
            )

    # ── Read operations ──────────────────────────────────────────────

    def get_by_prompt(
        self, prompt_id: int
    ) -> list[ActivationHistoryRecord]:
        """Return all activation records for a given prompt execution.

        Args:
            prompt_id: The ``prompt_history.id`` to filter by.

        Returns:
            List of :class:`ActivationHistoryRecord` ordered by layer number.
        """
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, prompt_id, layer_number, mean, std,
                       minimum, maximum, norm, tensor_shape, created_at
                FROM   activation_history
                WHERE  prompt_id = ?
                ORDER  BY layer_number ASC;
                """,
                (prompt_id,),
            ).fetchall()

        return [
            ActivationHistoryRecord(
                id=row["id"],
                prompt_id=row["prompt_id"],
                layer_number=row["layer_number"],
                mean=row["mean"],
                std=row["std"],
                minimum=row["minimum"],
                maximum=row["maximum"],
                norm=row["norm"],
                tensor_shape=row["tensor_shape"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def get_latest(self, limit: int = 50) -> list[ActivationHistoryRecord]:
        """Return the most recent activation records across all prompts.

        Args:
            limit: Maximum number of records to return.

        Returns:
            List of :class:`ActivationHistoryRecord` ordered newest first.
        """
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, prompt_id, layer_number, mean, std,
                       minimum, maximum, norm, tensor_shape, created_at
                FROM   activation_history
                ORDER  BY created_at DESC
                LIMIT  ?;
                """,
                (limit,),
            ).fetchall()

        return [
            ActivationHistoryRecord(
                id=row["id"],
                prompt_id=row["prompt_id"],
                layer_number=row["layer_number"],
                mean=row["mean"],
                std=row["std"],
                minimum=row["minimum"],
                maximum=row["maximum"],
                norm=row["norm"],
                tensor_shape=row["tensor_shape"],
                created_at=row["created_at"],
            )
            for row in rows
        ]
