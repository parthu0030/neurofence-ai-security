"""Scan summary repository for NeuroFence.

Encapsulates all SQLite operations for the ``scan_summary`` table.
Follows the repository pattern used by :mod:`database.activation_history`.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any

from database.models import ScanSummaryRecord

log = logging.getLogger(__name__)


class ScanSummaryRepository:
    """CRUD operations for the ``scan_summary`` table.

    Manages short-lived SQLite connections per operation to ensure
    thread safety and consistency with :class:`database.database.DatabaseManager`.

    Schema:
        id                 INTEGER PRIMARY KEY AUTOINCREMENT,
        model_id           INTEGER NOT NULL,
        scan_date          TEXT    NOT NULL,
        security_score     REAL    NOT NULL,
        overall_status     TEXT    NOT NULL,
        critical_count     INTEGER NOT NULL,
        high_count         INTEGER NOT NULL,
        medium_count       INTEGER NOT NULL,
        low_count          INTEGER NOT NULL,
        average_activation REAL    NOT NULL,
        peak_activation    REAL    NOT NULL,
        execution_time     REAL    NOT NULL,
        sha256             TEXT    NOT NULL
    """

    def __init__(self, db_path: Path | str) -> None:
        self._db_path = str(db_path)

    # ── Connection helper ────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ── Schema initialization ────────────────────────────────────────

    def create_table(self) -> None:
        """Ensure the ``scan_summary`` table exists."""
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scan_summary (
                    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id           INTEGER NOT NULL,
                    scan_date          TEXT    NOT NULL,
                    security_score     REAL    NOT NULL,
                    overall_status     TEXT    NOT NULL,
                    critical_count     INTEGER NOT NULL,
                    high_count         INTEGER NOT NULL,
                    medium_count       INTEGER NOT NULL,
                    low_count          INTEGER NOT NULL,
                    average_activation REAL    NOT NULL,
                    peak_activation    REAL    NOT NULL,
                    execution_time     REAL    NOT NULL,
                    sha256             TEXT    NOT NULL,
                    FOREIGN KEY (model_id) REFERENCES uploaded_models(id)
                );
                """
            )

    # ── Write operations ─────────────────────────────────────────────

    def insert(self, record: ScanSummaryRecord) -> int:
        """Insert a scan summary record and return its row ID."""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO scan_summary
                    (model_id, scan_date, security_score, overall_status,
                     critical_count, high_count, medium_count, low_count,
                     average_activation, peak_activation, execution_time, sha256)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    record.model_id,
                    record.scan_date,
                    record.security_score,
                    record.overall_status,
                    record.critical_count,
                    record.high_count,
                    record.medium_count,
                    record.low_count,
                    record.average_activation,
                    record.peak_activation,
                    record.execution_time,
                    record.sha256,
                ),
            )
            return cursor.lastrowid

    def delete(self, scan_id: int) -> bool:
        """Delete a scan summary by ID."""
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM scan_summary WHERE id = ?;",
                (scan_id,),
            )
            return cursor.rowcount > 0

    # ── Read operations ──────────────────────────────────────────────

    def get_by_id(self, scan_id: int) -> ScanSummaryRecord | None:
        """Return a scan summary record by primary key."""
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, model_id, scan_date, security_score, overall_status,
                       critical_count, high_count, medium_count, low_count,
                       average_activation, peak_activation, execution_time, sha256
                FROM   scan_summary
                WHERE  id = ?;
                """,
                (scan_id,),
            ).fetchone()

        if row is None:
            return None

        return ScanSummaryRecord(
            id=row["id"],
            model_id=row["model_id"],
            scan_date=row["scan_date"],
            security_score=row["security_score"],
            overall_status=row["overall_status"],
            critical_count=row["critical_count"],
            high_count=row["high_count"],
            medium_count=row["medium_count"],
            low_count=row["low_count"],
            average_activation=row["average_activation"],
            peak_activation=row["peak_activation"],
            execution_time=row["execution_time"],
            sha256=row["sha256"],
        )

    def get_all(self) -> list[ScanSummaryRecord]:
        """Return all scan summary records ordered newest first."""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, model_id, scan_date, security_score, overall_status,
                       critical_count, high_count, medium_count, low_count,
                       average_activation, peak_activation, execution_time, sha256
                FROM   scan_summary
                ORDER  BY scan_date DESC, id DESC;
                """
            ).fetchall()

        return [
            ScanSummaryRecord(
                id=row["id"],
                model_id=row["model_id"],
                scan_date=row["scan_date"],
                security_score=row["security_score"],
                overall_status=row["overall_status"],
                critical_count=row["critical_count"],
                high_count=row["high_count"],
                medium_count=row["medium_count"],
                low_count=row["low_count"],
                average_activation=row["average_activation"],
                peak_activation=row["peak_activation"],
                execution_time=row["execution_time"],
                sha256=row["sha256"],
            )
            for row in rows
        ]

    def get_summaries_with_model_info(self) -> list[dict[str, Any]]:
        """Return scan summaries joined with model filename and inspection architecture."""
        query = """
            SELECT
                s.id AS id,
                s.model_id AS model_id,
                COALESCE(m.filename, 'Unknown Model') AS filename,
                COALESCE(i.architecture, 'Standard Transformer') AS architecture,
                s.scan_date AS scan_date,
                s.security_score AS security_score,
                s.overall_status AS overall_status,
                s.critical_count AS critical_count,
                s.high_count AS high_count,
                s.medium_count AS medium_count,
                s.low_count AS low_count,
                (s.critical_count + s.high_count + s.medium_count + s.low_count) AS total_findings,
                s.average_activation AS average_activation,
                s.peak_activation AS peak_activation,
                s.execution_time AS execution_time,
                s.sha256 AS sha256
            FROM scan_summary s
            LEFT JOIN uploaded_models m ON s.model_id = m.id
            LEFT JOIN model_inspection i ON s.model_id = i.model_id
            ORDER BY s.scan_date DESC, s.id DESC;
        """
        with self._connect() as conn:
            rows = conn.execute(query).fetchall()

        return [dict(row) for row in rows]
