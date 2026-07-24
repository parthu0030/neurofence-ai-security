"""Multi-Scan Comparison Service for NeuroFence AI Security.

Provides side-by-side metric comparison, delta calculation, and highlight logic
(improvements vs regressions) between two security scans.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from services.scan_history_service import ScanHistoryService

log = logging.getLogger(__name__)


@dataclass
class ComparisonItem:
    """Represents a single metric comparison between Scan A and Scan B."""

    field_name: str
    val_a: Any
    val_b: Any
    difference: float | int | str
    difference_str: str
    is_improvement: bool | None  # True = improvement (green), False = regression (red), None = neutral
    unit: str = ""


@dataclass
class ScanComparisonResult:
    """Result object containing full comparison details between Scan A and Scan B."""

    scan_a: dict[str, Any]
    scan_b: dict[str, Any]
    metrics: list[ComparisonItem]
    summary_verdict: str


class ComparisonService:
    """Business logic for comparing two scan records side-by-side."""

    def __init__(self, history_service: ScanHistoryService | None = None) -> None:
        self._history_service = history_service or ScanHistoryService()

    def compare_scans(
        self,
        scan_id_a: int,
        scan_id_b: int,
    ) -> ScanComparisonResult:
        """Compare two scans given their row IDs."""
        if scan_id_a == scan_id_b:
            log.warning("Comparison attempted on identical scan ID %d", scan_id_a)

        scan_a = self._history_service.get_scan_by_id(scan_id_a)
        scan_b = self._history_service.get_scan_by_id(scan_id_b)

        if not scan_a:
            raise ValueError(f"Scan record with ID {scan_id_a} not found.")
        if not scan_b:
            raise ValueError(f"Scan record with ID {scan_id_b} not found.")

        return self.compare_scan_dicts(scan_a, scan_b)

    def compare_scan_dicts(
        self,
        scan_a: dict[str, Any],
        scan_b: dict[str, Any],
    ) -> ScanComparisonResult:
        """Compare two scan dictionaries."""
        items: list[ComparisonItem] = []

        # 1. Model Name
        val_a = scan_a.get("filename", "Unknown")
        val_b = scan_b.get("filename", "Unknown")
        items.append(
            ComparisonItem(
                field_name="Model Name",
                val_a=val_a,
                val_b=val_b,
                difference="—",
                difference_str="Identical" if val_a == val_b else "Different",
                is_improvement=None,
            )
        )

        # 2. SHA256
        sha_a = str(scan_a.get("sha256", "—"))[:12] + "..." if scan_a.get("sha256") else "—"
        sha_b = str(scan_b.get("sha256", "—"))[:12] + "..." if scan_b.get("sha256") else "—"
        items.append(
            ComparisonItem(
                field_name="SHA256 Fingerprint",
                val_a=sha_a,
                val_b=sha_b,
                difference="—",
                difference_str="Match" if scan_a.get("sha256") == scan_b.get("sha256") else "Mismatch",
                is_improvement=None,
            )
        )

        # 3. Architecture
        items.append(
            ComparisonItem(
                field_name="Architecture",
                val_a=scan_a.get("architecture", "—"),
                val_b=scan_b.get("architecture", "—"),
                difference="—",
                difference_str="Same" if scan_a.get("architecture") == scan_b.get("architecture") else "Diff",
                is_improvement=None,
            )
        )

        # 4. Security Score (Higher is better)
        score_a = float(scan_a.get("security_score", 0.0))
        score_b = float(scan_b.get("security_score", 0.0))
        diff_score = round(score_b - score_a, 1)
        items.append(
            ComparisonItem(
                field_name="Security Score",
                val_a=score_a,
                val_b=score_b,
                difference=diff_score,
                difference_str=f"{'+' if diff_score > 0 else ''}{diff_score}",
                is_improvement=True if diff_score > 0 else (False if diff_score < 0 else None),
                unit="/ 100",
            )
        )

        # 5. Critical Findings (Lower is better)
        c_a = int(scan_a.get("critical_count", 0))
        c_b = int(scan_b.get("critical_count", 0))
        diff_c = c_b - c_a
        items.append(
            ComparisonItem(
                field_name="Critical Findings",
                val_a=c_a,
                val_b=c_b,
                difference=diff_c,
                difference_str=f"{'+' if diff_c > 0 else ''}{diff_c}",
                is_improvement=True if diff_c < 0 else (False if diff_c > 0 else None),
            )
        )

        # 6. High Findings (Lower is better)
        h_a = int(scan_a.get("high_count", 0))
        h_b = int(scan_b.get("high_count", 0))
        diff_h = h_b - h_a
        items.append(
            ComparisonItem(
                field_name="High Findings",
                val_a=h_a,
                val_b=h_b,
                difference=diff_h,
                difference_str=f"{'+' if diff_h > 0 else ''}{diff_h}",
                is_improvement=True if diff_h < 0 else (False if diff_h > 0 else None),
            )
        )

        # 7. Medium Findings (Lower is better)
        m_a = int(scan_a.get("medium_count", 0))
        m_b = int(scan_b.get("medium_count", 0))
        diff_m = m_b - m_a
        items.append(
            ComparisonItem(
                field_name="Medium Findings",
                val_a=m_a,
                val_b=m_b,
                difference=diff_m,
                difference_str=f"{'+' if diff_m > 0 else ''}{diff_m}",
                is_improvement=True if diff_m < 0 else (False if diff_m > 0 else None),
            )
        )

        # 8. Low Findings (Lower is better)
        l_a = int(scan_a.get("low_count", 0))
        l_b = int(scan_b.get("low_count", 0))
        diff_l = l_b - l_a
        items.append(
            ComparisonItem(
                field_name="Low Findings",
                val_a=l_a,
                val_b=l_b,
                difference=diff_l,
                difference_str=f"{'+' if diff_l > 0 else ''}{diff_l}",
                is_improvement=True if diff_l < 0 else (False if diff_l > 0 else None),
            )
        )

        # 9. Average Activation (Magnitude comparison)
        avg_act_a = float(scan_a.get("average_activation", 0.0))
        avg_act_b = float(scan_b.get("average_activation", 0.0))
        diff_avg = round(avg_act_b - avg_act_a, 6)
        items.append(
            ComparisonItem(
                field_name="Average Activation",
                val_a=avg_act_a,
                val_b=avg_act_b,
                difference=diff_avg,
                difference_str=f"{'+' if diff_avg > 0 else ''}{diff_avg:.4f}",
                is_improvement=None,  # Activation shift is informational
            )
        )

        # 10. Peak Activation
        peak_a = float(scan_a.get("peak_activation", 0.0))
        peak_b = float(scan_b.get("peak_activation", 0.0))
        diff_peak = round(peak_b - peak_a, 6)
        items.append(
            ComparisonItem(
                field_name="Peak Activation",
                val_a=peak_a,
                val_b=peak_b,
                difference=diff_peak,
                difference_str=f"{'+' if diff_peak > 0 else ''}{diff_peak:.4f}",
                is_improvement=True if diff_peak < 0 else (False if diff_peak > 0 else None),
            )
        )

        # 11. Total Findings Count
        tot_a = c_a + h_a + m_a + l_a
        tot_b = c_b + h_b + m_b + l_b
        diff_tot = tot_b - tot_a
        items.append(
            ComparisonItem(
                field_name="Total Findings",
                val_a=tot_a,
                val_b=tot_b,
                difference=diff_tot,
                difference_str=f"{'+' if diff_tot > 0 else ''}{diff_tot}",
                is_improvement=True if diff_tot < 0 else (False if diff_tot > 0 else None),
            )
        )

        # 12. Execution Time (Lower is faster)
        time_a = float(scan_a.get("execution_time", 0.0))
        time_b = float(scan_b.get("execution_time", 0.0))
        diff_time = round(time_b - time_a, 3)
        items.append(
            ComparisonItem(
                field_name="Execution Time",
                val_a=time_a,
                val_b=time_b,
                difference=diff_time,
                difference_str=f"{'+' if diff_time > 0 else ''}{diff_time}s",
                is_improvement=True if diff_time < 0 else (False if diff_time > 0 else None),
                unit="s",
            )
        )

        # Generate summary verdict
        if diff_score > 0:
            verdict = f"Scan B shows an IMPROVEMENT of +{diff_score} points in Security Score over Scan A."
        elif diff_score < 0:
            verdict = f"Scan B shows a REGRESSION of {diff_score} points in Security Score compared to Scan A."
        else:
            verdict = "Both scans scored identically in overall security rating."

        return ScanComparisonResult(
            scan_a=scan_a,
            scan_b=scan_b,
            metrics=items,
            summary_verdict=verdict,
        )
