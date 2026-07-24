"""Scan History Page for NeuroFence AI Security.

Renders summary metrics cards, search/filter/sort toolbar, a professional
table of previous security scans, action controls (compare, delete), and
graphical history trends.
"""

from __future__ import annotations

import logging
from typing import Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
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
from services.scan_history_service import ScanHistoryMetrics, ScanHistoryService
from ui.cards import StatCard
from ui.styles import HISTORY_STYLESHEET
from visualization.history_charts import HistoryChartWidget

log = logging.getLogger(__name__)
_T = ThemeColors()


class ScanHistoryPage(QWidget):
    """Scan History page widget with search, sort, filter, and comparison triggers."""

    # Signal emitted when the user requests comparison of two scan IDs.
    compare_requested = pyqtSignal(int, int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("HistoryPanelContainer")
        self.setStyleSheet(HISTORY_STYLESHEET)

        self._history_service = ScanHistoryService()
        self._raw_scans: list[dict[str, Any]] = []
        self._displayed_scans: list[dict[str, Any]] = []
        self._selected_scan_ids: set[int] = set()

        self._build_ui()
        self.refresh_data()

    # ── UI Construction ───────────────────────────────────────────────

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll Area for page content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        container = QWidget()
        container.setStyleSheet(f"background-color: {_T.bg_dark};")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)

        # ── 1. Summary Cards Header (Feature 5) ──────────────────────
        self._cards_layout = QHBoxLayout()
        self._cards_layout.setSpacing(14)
        layout.addLayout(self._cards_layout)

        # ── 2. Toolbar (Search, Filter, Sort, Compare) ────────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setObjectName("HistorySearchInput")
        self.search_input.setPlaceholderText("🔍  Search scans by model, SHA256, status...")
        self.search_input.textChanged.connect(self._apply_filters)
        toolbar.addWidget(self.search_input)

        # Filter Dropdown
        self.filter_combo = QComboBox()
        self.filter_combo.setObjectName("HistoryFilterCombo")
        self.filter_combo.addItems([
            "All Statuses",
            "Clean",
            "Low Risk",
            "Medium Risk",
            "High Risk",
            "Critical Risk",
        ])
        self.filter_combo.currentTextChanged.connect(self._apply_filters)
        toolbar.addWidget(self.filter_combo)

        # Sort Dropdown
        self.sort_combo = QComboBox()
        self.sort_combo.setObjectName("HistorySortCombo")
        self.sort_combo.addItems([
            "Scan Date",
            "Security Score",
            "Model Name",
            "Overall Status",
            "Findings",
            "Execution Time",
        ])
        self.sort_combo.currentTextChanged.connect(self._apply_filters)
        toolbar.addWidget(self.sort_combo)

        # Sort Order Toggle
        self.sort_order_btn = QPushButton("⬇ Desc")
        self.sort_order_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sort_order_btn.setStyleSheet(f"background-color: {_T.bg_input}; color: {_T.text_primary}; border: 1px solid {_T.border}; border-radius: 8px; padding: 8px 12px;")
        self.sort_order_btn.clicked.connect(self._toggle_sort_order)
        self._descending = True
        toolbar.addWidget(self.sort_order_btn)

        toolbar.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Quick Compare Selected Button
        self.compare_btn = QPushButton("⚔️  Compare Selected (0)")
        self.compare_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.compare_btn.setStyleSheet(f"background-color: {_T.accent}; color: #ffffff; border: none; border-radius: 8px; padding: 8px 16px; font-weight: 600;")
        self.compare_btn.setEnabled(False)
        self.compare_btn.clicked.connect(self._on_compare_clicked)
        toolbar.addWidget(self.compare_btn)

        # Refresh Button
        refresh_btn = QPushButton("🔄  Refresh")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setStyleSheet(f"background-color: {_T.bg_input}; color: {_T.text_primary}; border: 1px solid {_T.border}; border-radius: 8px; padding: 8px 12px;")
        refresh_btn.clicked.connect(self.refresh_data)
        toolbar.addWidget(refresh_btn)

        layout.addLayout(toolbar)

        # ── 3. Scan History Table (Feature 2) ────────────────────────
        table_card = QFrame()
        table_card.setObjectName("HistoryCard")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(16, 16, 16, 16)
        table_layout.setSpacing(12)

        title_lbl = QLabel("📂  Scan History Records")
        title_lbl.setObjectName("HistorySectionTitle")
        table_layout.addWidget(title_lbl)

        self.table = QTableWidget()
        self.table.setObjectName("ScanHistoryTable")
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Select",
            "Scan Date",
            "Model Name",
            "Security Score",
            "Overall Status",
            "Findings",
            "Execution Time",
            "SHA256",
            "Actions",
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(False)
        self.table.setMinimumHeight(280)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)

        table_layout.addWidget(self.table)
        layout.addWidget(table_card)

        # ── 4. Graphical Trends Section (Feature 7) ───────────────────
        chart_card = QFrame()
        chart_card.setObjectName("HistoryChartCard")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(16, 16, 16, 16)
        chart_layout.setSpacing(12)

        chart_title = QLabel("📊  Multi-Scan Analytics & Trends")
        chart_title.setObjectName("HistorySectionTitle")
        chart_layout.addWidget(chart_title)

        self.charts_widget = HistoryChartWidget()
        chart_layout.addWidget(self.charts_widget)

        layout.addWidget(chart_card)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    # ── Public API / Refresh ─────────────────────────────────────────

    def refresh_data(self) -> None:
        """Fetch scan history from DB and refresh UI components."""
        try:
            self._raw_scans = self._history_service.get_all_scans()
            metrics = self._history_service.get_scan_metrics(self._raw_scans)
            self._render_summary_cards(metrics)
            self._apply_filters()
            self.charts_widget.update_charts(self._raw_scans)
        except Exception as exc:
            log.exception("Error refreshing scan history page: %s", exc)

    # ── Render Summary Cards (Feature 5) ─────────────────────────────

    def _render_summary_cards(self, metrics: ScanHistoryMetrics) -> None:
        # Clear old card layout items
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        cards_data = [
            ("📁", str(metrics.total_scans), "Total Scans", _T.accent),
            ("🛡️", f"{metrics.average_security_score:.1f}", "Avg Security Score", _T.success if metrics.average_security_score >= 80 else _T.warning),
            ("🏆", f"{metrics.highest_score:.1f}", "Highest Score", _T.success),
            ("⚠️", f"{metrics.lowest_score:.1f}", "Lowest Score", _T.danger if metrics.lowest_score < 60 else _T.warning),
            ("🕒", str(metrics.last_scan_date)[:10] if metrics.last_scan_date != "N/A" else "Never", "Last Scan Date", _T.info),
            ("🧠", str(metrics.total_models_tested), "Models Tested", _T.accent_light),
        ]

        for icon, val, lbl, color in cards_data:
            card = StatCard(icon, val, lbl, accent_color=color)
            card.setMinimumHeight(95)
            self._cards_layout.addWidget(card)

    # ── Filter, Search & Table Render ────────────────────────────────

    def _toggle_sort_order(self) -> None:
        self._descending = not self._descending
        self.sort_order_btn.setText("⬇ Desc" if self._descending else "⬆ Asc")
        self._apply_filters()

    def _apply_filters(self) -> None:
        query = self.search_input.text()
        status_filter = self.filter_combo.currentText()
        sort_field = self.sort_combo.currentText()

        filtered = self._history_service.filter_scans(self._raw_scans, status=status_filter)
        searched = self._history_service.search_scans(filtered, query)
        self._displayed_scans = self._history_service.sort_scans(searched, sort_by=sort_field, descending=self._descending)

        self._render_table()

    def _render_table(self) -> None:
        self.table.setRowCount(0)
        self.table.setRowCount(len(self._displayed_scans))

        risk_colors = {
            "Clean": _T.success,
            "Low Risk": _T.success,
            "Medium Risk": _T.warning,
            "High Risk": _T.danger,
            "Critical Risk": _T.danger,
        }

        for row_idx, scan in enumerate(self._displayed_scans):
            scan_id = int(scan.get("id", 0))

            # Col 0: Select Checkbox
            chk_widget = QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.setContentsMargins(4, 0, 4, 0)
            chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cb = QPushButton("☐" if scan_id not in self._selected_scan_ids else "☑")
            cb.setFixedWidth(32)
            cb.setStyleSheet("border: none; background: transparent; font-size: 16px; color: #3b82f6;")
            cb.setCursor(Qt.CursorShape.PointingHandCursor)
            cb.clicked.connect(lambda _chk, sid=scan_id: self._toggle_select_scan(sid))
            chk_layout.addWidget(cb)
            self.table.setCellWidget(row_idx, 0, chk_widget)

            # Col 1: Scan Date
            d_item = QTableWidgetItem(str(scan.get("scan_date", "—")))
            d_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row_idx, 1, d_item)

            # Col 2: Model Name
            m_item = QTableWidgetItem(str(scan.get("filename", "Unknown")))
            m_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row_idx, 2, m_item)

            # Col 3: Security Score
            score = float(scan.get("security_score", 0.0))
            score_item = QTableWidgetItem(f"{score:.1f}")
            score_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            score_item.setForeground(QColor(_T.success if score >= 80 else (_T.warning if score >= 60 else _T.danger)))
            self.table.setItem(row_idx, 3, score_item)

            # Col 4: Overall Status
            status = str(scan.get("overall_status", "Unknown"))
            st_item = QTableWidgetItem(status)
            st_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            st_item.setForeground(QColor(risk_colors.get(status, _T.text_primary)))
            self.table.setItem(row_idx, 4, st_item)

            # Col 5: Findings Count
            tot_f = int(scan.get("total_findings", 0))
            f_item = QTableWidgetItem(str(tot_f))
            f_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row_idx, 5, f_item)

            # Col 6: Execution Time
            e_time = float(scan.get("execution_time", 0.0))
            t_item = QTableWidgetItem(f"{e_time:.2f}s")
            t_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row_idx, 6, t_item)

            # Col 7: SHA256
            sha = str(scan.get("sha256", "—"))
            sha_disp = sha[:12] + "..." if len(sha) > 12 else sha
            s_item = QTableWidgetItem(sha_disp)
            s_item.setToolTip(sha)
            s_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row_idx, 7, s_item)

            # Col 8: Actions (Delete)
            act_widget = QWidget()
            act_layout = QHBoxLayout(act_widget)
            act_layout.setContentsMargins(2, 0, 2, 0)
            act_layout.setSpacing(6)

            del_btn = QPushButton("🗑️")
            del_btn.setToolTip("Delete Scan")
            del_btn.setFixedWidth(28)
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.setStyleSheet("border: none; background: transparent; font-size: 14px;")
            del_btn.clicked.connect(lambda _chk, sid=scan_id: self._on_delete_scan(sid))
            act_layout.addWidget(del_btn)

            self.table.setCellWidget(row_idx, 8, act_widget)

    # ── Selection & Actions ──────────────────────────────────────────

    def _toggle_select_scan(self, scan_id: int) -> None:
        if scan_id in self._selected_scan_ids:
            self._selected_scan_ids.remove(scan_id)
        else:
            if len(self._selected_scan_ids) >= 2:
                # Keep max 2 selected — pop oldest
                self._selected_scan_ids.pop()
            self._selected_scan_ids.add(scan_id)

        count = len(self._selected_scan_ids)
        self.compare_btn.setText(f"⚔️  Compare Selected ({count})")
        self.compare_btn.setEnabled(count == 2)
        self._render_table()

    def _on_compare_clicked(self) -> None:
        if len(self._selected_scan_ids) == 2:
            ids = list(self._selected_scan_ids)
            self.compare_requested.emit(ids[0], ids[1])

    def _on_delete_scan(self, scan_id: int) -> None:
        reply = QMessageBox.question(
            self,
            "Delete Scan Record",
            f"Are you sure you want to delete scan record #{scan_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._history_service.delete_scan(scan_id)
            if scan_id in self._selected_scan_ids:
                self._selected_scan_ids.remove(scan_id)
            self.refresh_data()
