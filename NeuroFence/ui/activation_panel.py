"""Activation Tracking panel for NeuroFence.

Full-page widget providing:
- Activation status cards (hooks, layers, avg, peak, status)
- Per-layer statistics table
- Matplotlib chart visualization

This widget communicates with the service layer through
:class:`ActivationTrackerService` and never touches the database
directly.
"""

from __future__ import annotations

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config.settings import ThemeColors
from ui.styles import ACTIVATION_PANEL_STYLESHEET

log = logging.getLogger(__name__)
_T = ThemeColors()


class ActivationPanel(QWidget):
    """Full-page Activation Tracking widget.

    Composed of three stacked cards:
    1. Activation Status  — summary stat boxes
    2. Layer Statistics   — per-layer table
    3. Visualization      — matplotlib charts
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ActivationPanelContainer")
        self.setStyleSheet(ACTIVATION_PANEL_STYLESHEET)
        self._build_ui()

    # ── Public API ───────────────────────────────────────────────────

    def update_activation_data(self, summary) -> None:
        """Populate all three cards from an :class:`ActivationSummary`.

        Args:
            summary: An ``ActivationSummary`` from the tracker service.
        """
        if summary is None:
            return

        # Card 1 — status boxes
        self._stat_labels["Hooks Registered"].setText("✔ Active")
        self._stat_labels["Hooks Registered"].setObjectName("ActivationStatusSuccess")
        self._restyle(self._stat_labels["Hooks Registered"])

        self._stat_labels["Layers Captured"].setText(str(summary.layers_captured))
        self._stat_labels["Average Activation"].setText(f"{summary.average_activation:.6f}")
        self._stat_labels["Peak Activation"].setText(f"{summary.peak_activation:.4f}")

        status_lbl = self._stat_labels["Capture Status"]
        if summary.capture_successful:
            status_lbl.setText("✔ Capture Successful")
            status_lbl.setObjectName("ActivationStatusSuccess")
        else:
            status_lbl.setText("✖ Capture Failed")
            status_lbl.setObjectName("ActivationStatusError")
        self._restyle(status_lbl)

        # Card 2 — layer table
        self._populate_layer_table(summary.layers)

        # Card 3 — charts
        self._chart_widget.update_charts(summary)

    def clear(self) -> None:
        """Reset the panel to its placeholder state."""
        for lbl in self._stat_labels.values():
            lbl.setText("—")
            lbl.setObjectName("ActivationStatValue")
            self._restyle(lbl)
        self._layer_table.setRowCount(0)

    # ── UI construction ──────────────────────────────────────────────

    def _build_ui(self) -> None:
        # Scrollable wrapper
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        container = QWidget()
        container.setStyleSheet(f"background-color: {_T.bg_dark};")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        # Page title
        page_title = QLabel("⚡  Activation Tracking Engine")
        page_title.setStyleSheet(
            f"color: {_T.text_primary}; font-size: 20px; font-weight: 700;"
        )
        layout.addWidget(page_title)

        page_sub = QLabel(
            "Visualize internal neural activations captured via PyTorch forward hooks."
        )
        page_sub.setStyleSheet(
            f"color: {_T.text_secondary}; font-size: 13px;"
        )
        layout.addWidget(page_sub)

        # ── Card 1: Activation Status ─────────────────────────────────
        layout.addWidget(self._build_status_card())

        # ── Card 2: Layer Statistics ──────────────────────────────────
        layout.addWidget(self._build_layer_table_card())

        # ── Card 3: Visualization ─────────────────────────────────────
        layout.addWidget(self._build_chart_card())

        # Stretch bottom
        layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        scroll.setWidget(container)
        outer.addWidget(scroll)

    # ── Card 1: Activation Status ────────────────────────────────────

    def _build_status_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("ActivationStatusCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("🧠  Activation Status")
        title.setObjectName("ActivationSectionTitle")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(10)

        self._stat_labels: dict[str, QLabel] = {}

        stat_defs = [
            ("Hooks Registered", 0, 0),
            ("Layers Captured", 0, 1),
            ("Average Activation", 0, 2),
            ("Peak Activation", 1, 0),
            ("Capture Status", 1, 1),
        ]

        for label_text, row, col in stat_defs:
            box = QFrame()
            box.setObjectName("ActivationStatBox")
            box_layout = QVBoxLayout(box)
            box_layout.setContentsMargins(14, 10, 14, 10)
            box_layout.setSpacing(4)

            lbl = QLabel(label_text)
            lbl.setObjectName("ActivationStatLabel")
            box_layout.addWidget(lbl)

            val = QLabel("—")
            val.setObjectName("ActivationStatValue")
            self._stat_labels[label_text] = val
            box_layout.addWidget(val)

            grid.addWidget(box, row, col)

        layout.addLayout(grid)
        return card

    # ── Card 2: Layer Statistics Table ────────────────────────────────

    def _build_layer_table_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("LayerTableCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("📊  Layer Statistics")
        title.setObjectName("ActivationSectionTitle")
        layout.addWidget(title)

        headers = ["Layer", "Mean", "Std Dev", "Max", "Min", "L2 Norm", "Shape"]
        self._layer_table = QTableWidget(0, len(headers))
        self._layer_table.setHorizontalHeaderLabels(headers)
        self._layer_table.verticalHeader().setVisible(False)
        self._layer_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._layer_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._layer_table.setShowGrid(False)
        self._layer_table.setAlternatingRowColors(False)
        self._layer_table.setMinimumHeight(200)

        h_header = self._layer_table.horizontalHeader()
        h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        h_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        h_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        h_header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        h_header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self._layer_table)
        return card

    # ── Card 3: Visualization ────────────────────────────────────────

    def _build_chart_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("ActivationChartCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("📈  Activation Visualization")
        title.setObjectName("ActivationSectionTitle")
        layout.addWidget(title)

        # Lazy import to avoid pulling in matplotlib at module level
        from visualization.activation_charts import ActivationChartWidget

        self._chart_widget = ActivationChartWidget()
        self._chart_widget.setMinimumHeight(500)
        layout.addWidget(self._chart_widget)

        return card

    # ── Table population ─────────────────────────────────────────────

    def _populate_layer_table(self, layers: list) -> None:
        """Fill the layer table from a list of ``LayerActivation`` objects."""
        self._layer_table.setRowCount(len(layers))

        for row_idx, la in enumerate(layers):
            cells = [
                (f"Layer {la.layer_number}", None),
                (f"{la.mean:.6f}", la.mean),
                (f"{la.std:.6f}", None),
                (f"{la.max:.4f}", None),
                (f"{la.min:.4f}", None),
                (f"{la.norm:.4f}", None),
                (la.tensor_shape, None),
            ]

            for col_idx, (text, _val) in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setFlags(
                    Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
                )
                self._layer_table.setItem(row_idx, col_idx, item)

    # ── Helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _restyle(widget: QWidget) -> None:
        """Force Qt stylesheet re-evaluation on *widget*."""
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()
