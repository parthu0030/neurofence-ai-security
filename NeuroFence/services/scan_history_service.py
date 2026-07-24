"""Scan History Service for NeuroFence AI Security.

Manages loading, filtering, searching, sorting, deleting, and calculating
summary metrics for completed security scans.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from database.database import DatabaseManager
from database.models import ScanSummaryRecord

log = logging.getLogger(__name__)


@dataclass
class ScanHistoryMetrics:
    """Summary statistics across all completed security scans."""

    total_scans: int = 0
    average_security_score: float = 0.0
    highest_score: float = 0.0
    lowest_score: float = 0.0
    last_scan_date: str = "N/A"
    total_models_tested: int = 0


class ScanHistoryService:
    """Business logic for scan history persistence, retrieval, and statistics."""

    def __init__(self, db_manager: DatabaseManager | None = None) -> None:
        self._db = db_manager or DatabaseManager()

    # ── Storage & Deletion ───────────────────────────────────────────

    def store_scan(
        self,
        *,
        model_id: int,
        scan_date: str | None = None,
        security_score: float,
        overall_status: str,
        critical_count: int,
        high_count: int,
        medium_count: int,
        low_count: int,
        average_activation: float = 0.0,
        peak_activation: float = 0.0,
        execution_time: float = 0.0,
        sha256: str = "",
    ) -> int:
        """Store a completed scan summary into the database."""
        if not scan_date:
            scan_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        record = ScanSummaryRecord(
            model_id=model_id,
            scan_date=scan_date,
            security_score=round(float(security_score), 2),
            overall_status=overall_status,
            critical_count=int(critical_count),
            high_count=int(high_count),
            medium_count=int(medium_count),
            low_count=int(low_count),
            average_activation=round(float(average_activation), 6),
            peak_activation=round(float(peak_activation), 6),
            execution_time=round(float(execution_time), 3),
            sha256=sha256,
        )

        try:
            scan_id = self._db.insert_scan_summary(record)
            log.info("Persisted scan summary ID %d for model_id %d", scan_id, model_id)
            return scan_id
        except Exception as exc:
            log.exception("Failed to store scan summary: %s", exc)
            raise

    def delete_scan(self, scan_id: int) -> bool:
        """Delete a scan record from the database."""
        try:
            success = self._db.delete_scan_summary(scan_id)
            if success:
                log.info("Deleted scan record ID %d", scan_id)
            else:
                log.warning("No scan record found for deletion with ID %d", scan_id)
            return success
        except Exception as exc:
            log.exception("Error deleting scan ID %d: %s", scan_id, exc)
            return False

    # ── Retrieval ────────────────────────────────────────────────────

    def get_all_scans(self) -> list[dict[str, Any]]:
        """Return all scan summaries with joined model metadata."""
        try:
            return self._db.get_scan_summaries_with_model_info()
        except Exception as exc:
            log.exception("Failed to load scan history: %s", exc)
            return []

    def get_scan_by_id(self, scan_id: int) -> dict[str, Any] | None:
        """Return a single scan dictionary by ID."""
        scans = self.get_all_scans()
        for scan in scans:
            if scan.get("id") == scan_id:
                return scan
        return None

    # ── Filter, Search & Sort ────────────────────────────────────────

    @staticmethod
    def filter_scans(
        scans: list[dict[str, Any]],
        *,
        status: str | None = None,
        model_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """Filter scan records by status or model name."""
        filtered = list(scans)

        if status and status.strip() and status.strip() != "All Statuses":
            target_status = status.strip().lower()
            filtered = [
                s for s in filtered
                if target_status in str(s.get("overall_status", "")).lower()
            ]

        if model_name and model_name.strip():
            target_name = model_name.strip().lower()
            filtered = [
                s for s in filtered
                if target_name in str(s.get("filename", "")).lower()
            ]

        return filtered

    @staticmethod
    def search_scans(scans: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
        """Search scan records matching query in filename, SHA256, or status."""
        if not query or not query.strip():
            return list(scans)

        q = query.strip().lower()
        results = []
        for s in scans:
            filename = str(s.get("filename", "")).lower()
            sha256 = str(s.get("sha256", "")).lower()
            status = str(s.get("overall_status", "")).lower()
            arch = str(s.get("architecture", "")).lower()
            if q in filename or q in sha256 or q in status or q in arch:
                results.append(s)
        return results

    @staticmethod
    def sort_scans(
        scans: list[dict[str, Any]],
        *,
        sort_by: str = "scan_date",
        descending: bool = True,
    ) -> list[dict[str, Any]]:
        """Sort scan records by date, security_score, model_name, status, findings, or execution_time."""
        key_map = {
            "Scan Date": "scan_date",
            "scan_date": "scan_date",
            "Model Name": "filename",
            "filename": "filename",
            "Security Score": "security_score",
            "security_score": "security_score",
            "Overall Status": "overall_status",
            "overall_status": "overall_status",
            "Findings": "total_findings",
            "total_findings": "total_findings",
            "Execution Time": "execution_time",
            "execution_time": "execution_time",
        }

        attr = key_map.get(sort_by, "scan_date")

        def sort_key(s: dict[str, Any]):
            val = s.get(attr)
            if val is None:
                return "" if isinstance(val, str) else 0
            return val

        return sorted(scans, key=sort_key, reverse=descending)

    # ── Summary Metrics ──────────────────────────────────────────────

    def get_scan_metrics(self, scans: list[dict[str, Any]] | None = None) -> ScanHistoryMetrics:
        """Compute aggregated metrics across scans for Scan Summary Cards."""
        if scans is None:
            scans = self.get_all_scans()

        if not scans:
            return ScanHistoryMetrics()

        scores = [float(s.get("security_score", 0.0)) for s in scans]
        models = {s.get("model_id") for s in scans if s.get("model_id") is not None}

        # Date of most recent scan
        sorted_dates = sorted([str(s.get("scan_date", "")) for s in scans if s.get("scan_date")], reverse=True)
        last_date = sorted_dates[0] if sorted_dates else "N/A"

        return ScanHistoryMetrics(
            total_scans=len(scans),
            average_security_score=round(sum(scores) / len(scores), 1) if scores else 0.0,
            highest_score=round(max(scores), 1) if scores else 0.0,
            lowest_score=round(min(scores), 1) if scores else 0.0,
            last_scan_date=last_date,
            total_models_tested=len(models),
        )
