"""Multi-Scan Comparison Page for NeuroFence AI Security.

Allows selecting two scans side-by-side to compare model details, security scores,
finding counts by severity, activation magnitudes, and execution times with
color-coded highlights for improvements and regressions.
"""

from __future__ import annotations

import logging
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config.settings import ThemeColors
from services.comparison_service import ComparisonItem, ComparisonService, ScanComparisonResult
from services.scan_history_service import ScanHistoryService
from ui.styles import COMPARISON_STYLESHEET

log = logging.getLogger(__name__)
_T = ThemeColors()


class ComparisonPage(QWidget):
    """Page widget for comparing two model scans side-by-side."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ComparisonPanelContainer")
        self.setStyleSheet(COMPARISON_STYLESHEET)

        self._history_service = ScanHistoryService()
        self._comparison_service = ComparisonService(self._history_service)
        self._available_scans: list[dict[str, Any]] = []

        self._build_ui()
        self.refresh_scans_list()

    # ── UI Construction ───────────────────────────────────────────────

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        container = QWidget()
        container.setStyleSheet(f"background-color: {_T.bg_dark};")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)

        # Title Header
        title_lbl = QLabel("⚔️  Multi-Scan Side-by-Side Comparison")
        title_lbl.setObjectName("ComparisonTitle")
        layout.addWidget(title_lbl)

        # ── 1. Selection Bar Card ──────────────────────────────────────
        sel_card = QFrame()
        sel_card.setObjectName("ComparisonSelectorCard")
        sel_layout = QHBoxLayout(sel_card)
        sel_layout.setContentsMargins(20, 16, 20, 16)
        sel_layout.setSpacing(16)

        # Scan A dropdown
        lbl_a = QLabel("Baseline Scan (A):")
        lbl_a.setStyleSheet(f"color: {_T.text_secondary}; font-weight: 600;")
        self.combo_a = QComboBox()
        self.combo_a.setObjectName("ScanSelectorCombo")
        sel_layout.addWidget(lbl_a)
        sel_layout.addWidget(self.combo_a)

        vs_lbl = QLabel("VS")
        vs_lbl.setStyleSheet(f"color: {_T.accent_light}; font-weight: 800; font-size: 14px;")
        sel_layout.addWidget(vs_lbl)

        # Scan B dropdown
        lbl_b = QLabel("Target Scan (B):")
        lbl_b.setStyleSheet(f"color: {_T.text_secondary}; font-weight: 600;")
        self.combo_b = QComboBox()
        self.combo_b.setObjectName("ScanSelectorCombo")
        sel_layout.addWidget(lbl_b)
        sel_layout.addWidget(self.combo_b)

        sel_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Compare Button
        self.compare_btn = QPushButton("⚡  Compare Now")
        self.compare_btn.setObjectName("CompareBtn")
        self.compare_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.compare_btn.clicked.connect(self._on_compare_button_clicked)
        sel_layout.addWidget(self.compare_btn)

        layout.addWidget(sel_card)

        # ── 2. Summary Verdict Box ────────────────────────────────────
        self.verdict_box = QFrame()
        self.verdict_box.setObjectName("VerdictBox")
        verdict_layout = QHBoxLayout(self.verdict_box)
        verdict_layout.setContentsMargins(16, 12, 16, 12)
        
        self.verdict_label = QLabel("Select two scans above to initiate side-by-side analysis.")
        self.verdict_label.setObjectName("VerdictText")
        verdict_layout.addWidget(self.verdict_label)
        layout.addWidget(self.verdict_box)

        # ── 3. Side-by-Side Comparison Table ─────────────────────────
        table_card = QFrame()
        table_card.setObjectName("ComparisonCard")
        t_layout = QVBoxLayout(table_card)
        t_layout.setContentsMargins(16, 16, 16, 16)
        t_layout.setSpacing(12)

        t_title = QLabel("📊  Detailed Metric Comparison & Delta Analysis")
        t_title.setObjectName("ComparisonTitle")
        t_layout.addWidget(t_title)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Metric",
            "Scan A (Baseline)",
            "Scan B (Target)",
            "Difference (B - A)",
            "Evaluation",
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setShowGrid(False)
        self.table.setMinimumHeight(380)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        t_layout.addWidget(self.table)
        layout.addWidget(table_card)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    # ── Public API & Populate Dropdowns ───────────────────────────────

    def refresh_scans_list(self) -> None:
        """Fetch all available scans from DB and populate selector comboboxes."""
        try:
            self._available_scans = self._history_service.get_all_scans()
            self.combo_a.clear()
            self.combo_b.clear()

            if not self._available_scans:
                self.combo_a.addItem("No scans available", None)
                self.combo_b.addItem("No scans available", None)
                self.compare_btn.setEnabled(False)
                return

            self.compare_btn.setEnabled(True)
            for scan in self._available_scans:
                sid = scan.get("id")
                date = str(scan.get("scan_date", ""))[:16]
                model = scan.get("filename", "Unknown")
                score = scan.get("security_score", 0.0)
                display_text = f"#{sid} | {model} | Score: {score:.1f} ({date})"

                self.combo_a.addItem(display_text, sid)
                self.combo_b.addItem(display_text, sid)

            # Default: Scan A = 2nd latest, Scan B = latest (if at least 2 exist)
            if len(self._available_scans) >= 2:
                self.combo_a.setCurrentIndex(1)
                self.combo_b.setCurrentIndex(0)

        except Exception as exc:
            log.exception("Failed to populate comparison scan selectors: %s", exc)

    def load_comparison(self, scan_id_a: int, scan_id_b: int) -> None:
        """Set dropdown selectors to specified scan IDs and trigger comparison."""
        self.refresh_scans_list()

        # Find indexes
        idx_a = -1
        idx_b = -1
        for i in range(self.combo_a.count()):
            if self.combo_a.itemData(i) == scan_id_a:
                idx_a = i
            if self.combo_b.itemData(i) == scan_id_b:
                idx_b = i

        if idx_a != -1:
            self.combo_a.setCurrentIndex(idx_a)
        if idx_b != -1:
            self.combo_b.setCurrentIndex(idx_b)

        self._execute_comparison(scan_id_a, scan_id_b)

    # ── Handlers & Rendering ──────────────────────────────────────────

    def _on_compare_button_clicked(self) -> None:
        id_a = self.combo_a.currentData()
        id_b = self.combo_b.currentData()

        if id_a is None or id_b is None:
            QMessageBox.warning(self, "No Scans Selected", "Please select two valid scans to compare.")
            return

        if id_a == id_b:
            QMessageBox.information(self, "Same Scan Selected", "You have selected the same scan for both baseline and target. Differences will be zero.")

        self._execute_comparison(id_a, id_b)

    def _execute_comparison(self, scan_id_a: int, scan_id_b: int) -> None:
        try:
            result = self._comparison_service.compare_scans(scan_id_a, scan_id_b)
            self._render_comparison_results(result)
        except Exception as exc:
            log.exception("Error executing multi-scan comparison: %s", exc)
            QMessageBox.critical(self, "Comparison Failure", f"Failed to perform comparison:\n\n{exc}")

    def _render_comparison_results(self, result: ScanComparisonResult) -> None:
        # Render Verdict
        self.verdict_label.setText(f"💡 {result.summary_verdict}")

        # Render Table Rows
        self.table.setRowCount(0)
        self.table.setRowCount(len(result.metrics))

        for row_idx, item in enumerate(result.metrics):
            # Col 0: Metric Name
            m_item = QTableWidgetItem(item.field_name)
            m_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            m_item.setStyleSheet("font-weight: 600;")
            self.table.setItem(row_idx, 0, m_item)

            # Col 1: Scan A
            va_str = f"{item.val_a}{item.unit if item.unit else ''}"
            a_item = QTableWidgetItem(va_str)
            a_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row_idx, 1, a_item)

            # Col 2: Scan B
            vb_str = f"{item.val_b}{item.unit if item.unit else ''}"
            b_item = QTableWidgetItem(vb_str)
            b_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row_idx, 2, b_item)

            # Col 3: Difference
            diff_item = QTableWidgetItem(item.difference_str)
            diff_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row_idx, 3, diff_item)

            # Col 4: Evaluation Badge
            eval_widget = QWidget()
            eval_layout = QHBoxLayout(eval_widget)
            eval_layout.setContentsMargins(4, 2, 4, 2)
            eval_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            lbl = QLabel()
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            if item.is_improvement is True:
                lbl.setText("✔ IMPROVEMENT")
                lbl.setStyleSheet("background-color: rgba(34, 197, 94, 0.15); color: #22c55e; border-radius: 4px; padding: 4px 8px; font-weight: 700; font-size: 11px;")
                diff_item.setForeground(QColor(_T.success))
            elif item.is_improvement is False:
                lbl.setText("✖ REGRESSION")
                lbl.setStyleSheet("background-color: rgba(239, 68, 68, 0.15); color: #ef4444; border-radius: 4px; padding: 4px 8px; font-weight: 700; font-size: 11px;")
                diff_item.setForeground(QColor(_T.danger))
            else:
                lbl.setText("— NEUTRAL")
                lbl.setStyleSheet(f"background-color: {_T.bg_input}; color: {_T.text_muted}; border-radius: 4px; padding: 4px 8px; font-size: 11px;")
                diff_item.setForeground(QColor(_T.text_secondary))

            eval_layout.addWidget(lbl)
            self.table.setCellWidget(row_idx, 4, eval_widget)
