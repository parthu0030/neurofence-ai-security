"""Unit test suite for NeuroFence Scan History & Multi-Scan Comparison System.

Tests database repository, service business logic, filter/search/sort, metrics,
and side-by-side comparison calculations.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from database.database import DatabaseManager
from database.models import ModelRecord, ScanSummaryRecord
from database.scan_summary import ScanSummaryRepository
from services.comparison_service import ComparisonService
from services.scan_history_service import ScanHistoryService


class TestScanHistoryAndComparison(unittest.TestCase):
    """Test cases for scan summary repository, history service, and comparison service."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_neurofence.db"
        self.db = DatabaseManager(self.db_path)
        self.history_service = ScanHistoryService(self.db)
        self.comparison_service = ComparisonService(self.history_service)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    # ── Database & Repository Tests ───────────────────────────────────

    def test_repository_crud(self) -> None:
        repo = ScanSummaryRepository(self.db_path)
        repo.create_table()

        record = ScanSummaryRecord(
            model_id=1,
            scan_date="2026-07-24 10:00:00",
            security_score=92.5,
            overall_status="Clean",
            critical_count=0,
            high_count=0,
            medium_count=1,
            low_count=2,
            average_activation=0.01542,
            peak_activation=2.451,
            execution_time=1.25,
            sha256="abc123def4567890",
        )

        # Insert
        row_id = repo.insert(record)
        self.assertGreater(row_id, 0)

        # Get by ID
        fetched = repo.get_by_id(row_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.security_score, 92.5)
        self.assertEqual(fetched.overall_status, "Clean")
        self.assertEqual(fetched.sha256, "abc123def4567890")

        # Get All
        all_records = repo.get_all()
        self.assertEqual(len(all_records), 1)

        # Delete
        success = repo.delete(row_id)
        self.assertTrue(success)
        self.assertIsNone(repo.get_by_id(row_id))

    # ── ScanHistoryService Tests ─────────────────────────────────────

    def test_history_service_operations(self) -> None:
        # Seed two dummy model records
        m1 = ModelRecord(
            filename="tinyllama-1.1b.safetensors",
            filepath="/tmp/tinyllama.safetensors",
            extension=".safetensors",
            size=1024,
            sha256="hash111",
            created_at="2026-07-24",
            modified_at="2026-07-24",
            uploaded_at="2026-07-24",
        )
        m2 = ModelRecord(
            filename="llama-7b-vulnerable.bin",
            filepath="/tmp/llama7b.bin",
            extension=".bin",
            size=2048,
            sha256="hash222",
            created_at="2026-07-24",
            modified_at="2026-07-24",
            uploaded_at="2026-07-24",
        )
        self.db.insert_model(m1)
        self.db.insert_model(m2)

        # Store scan 1 (Good score)
        id1 = self.history_service.store_scan(
            model_id=1,
            scan_date="2026-07-24 10:00:00",
            security_score=92.0,
            overall_status="Clean",
            critical_count=0,
            high_count=0,
            medium_count=1,
            low_count=1,
            average_activation=0.012,
            peak_activation=1.8,
            execution_time=1.1,
            sha256="hash111",
        )

        # Store scan 2 (Poor score)
        id2 = self.history_service.store_scan(
            model_id=2,
            scan_date="2026-07-24 11:00:00",
            security_score=71.0,
            overall_status="High Risk",
            critical_count=2,
            high_count=3,
            medium_count=1,
            low_count=0,
            average_activation=0.045,
            peak_activation=4.5,
            execution_time=2.3,
            sha256="hash222",
        )

        scans = self.history_service.get_all_scans()
        self.assertEqual(len(scans), 2)

        # Test Search
        search_res = self.history_service.search_scans(scans, "tinyllama")
        self.assertEqual(len(search_res), 1)
        self.assertEqual(search_res[0]["filename"], "tinyllama-1.1b.safetensors")

        # Test Filter
        filter_res = self.history_service.filter_scans(scans, status="High Risk")
        self.assertEqual(len(filter_res), 1)
        self.assertEqual(filter_res[0]["security_score"], 71.0)

        # Test Sort
        sorted_scans = self.history_service.sort_scans(scans, sort_by="security_score", descending=True)
        self.assertEqual(sorted_scans[0]["security_score"], 92.0)
        self.assertEqual(sorted_scans[1]["security_score"], 71.0)

        # Test Metrics
        metrics = self.history_service.get_scan_metrics(scans)
        self.assertEqual(metrics.total_scans, 2)
        self.assertEqual(metrics.average_security_score, 81.5)
        self.assertEqual(metrics.highest_score, 92.0)
        self.assertEqual(metrics.lowest_score, 71.0)
        self.assertEqual(metrics.total_models_tested, 2)

    # ── ComparisonService Tests ──────────────────────────────────────

    def test_comparison_service(self) -> None:
        scan_a = {
            "id": 1,
            "filename": "model-v1.safetensors",
            "architecture": "LlamaForCausalLM",
            "security_score": 92.0,
            "overall_status": "Clean",
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 1,
            "low_count": 2,
            "average_activation": 0.015,
            "peak_activation": 2.0,
            "total_findings": 3,
            "execution_time": 1.2,
            "sha256": "1111111111111111",
        }
        scan_b = {
            "id": 2,
            "filename": "model-v2.safetensors",
            "architecture": "LlamaForCausalLM",
            "security_score": 71.0,
            "overall_status": "High Risk",
            "critical_count": 2,
            "high_count": 1,
            "medium_count": 0,
            "low_count": 0,
            "average_activation": 0.045,
            "peak_activation": 4.5,
            "total_findings": 3,
            "execution_time": 2.5,
            "sha256": "2222222222222222",
        }

        res = self.comparison_service.compare_scan_dicts(scan_a, scan_b)

        self.assertIn("REGRESSION of -21.0 points", res.summary_verdict)

        metric_map = {item.field_name: item for item in res.metrics}
        self.assertEqual(metric_map["Security Score"].difference, -21.0)
        self.assertFalse(metric_map["Security Score"].is_improvement)  # Regression

        self.assertEqual(metric_map["Critical Findings"].difference, 2)
        self.assertFalse(metric_map["Critical Findings"].is_improvement)  # Critical findings increased = regression

        self.assertEqual(metric_map["Execution Time"].difference, 1.3)
        self.assertFalse(metric_map["Execution Time"].is_improvement)  # Slower execution time = regression


if __name__ == "__main__":
    unittest.main()
