"""Main dashboard compositor for NeuroFence.

Assembles the sidebar, header, stat cards, quick-scan panel,
recent-activity table, right-side info panel, and bottom status bar
into the final dashboard layout.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from config.settings import ThemeColors
from ui.cards import InfoPanelCard, QuickScanCard, RecentActivityCard, StatCard
from ui.header import HeaderWidget
from ui.sidebar import SidebarWidget
from ui.statusbar import StatusBarWidget

_T = ThemeColors()


class DashboardWindow(QWidget):
    """Top-level widget compositing every dashboard component.

    This widget is set as the ``centralWidget`` of the ``QMainWindow``
    in ``app.py``.  It owns the sidebar, header, content area, and
    status bar and wires them together with layout managers.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._connect_signals()

    # ── Layout construction ────────────────────────────────────────

    def _build_ui(self) -> None:
        # Root layout — sidebar | right column
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ──
        self.sidebar = SidebarWidget()
        root.addWidget(self.sidebar)

        # ── Right column: header + content + status bar ──
        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(0)

        # Header
        self.header = HeaderWidget()
        right_col.addWidget(self.header)

        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content = self._build_content_area()
        scroll.setWidget(content)
        right_col.addWidget(scroll, stretch=1)

        # Status bar
        self.status_bar = StatusBarWidget()
        right_col.addWidget(self.status_bar)

        root.addLayout(right_col, stretch=1)

    # ── Content area ───────────────────────────────────────────────

    def _build_content_area(self) -> QWidget:
        """Construct the main content body inside the scroll area."""
        container = QWidget()
        container.setStyleSheet(f"background-color: {_T.bg_dark};")

        outer = QHBoxLayout(container)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(20)

        # ── Centre column (stat cards + quick scan + activity) ──
        centre = QVBoxLayout()
        centre.setSpacing(20)

        # Stat cards row
        centre.addLayout(self._build_stat_cards())

        # Quick scan + Activity side-by-side
        mid_row = QHBoxLayout()
        mid_row.setSpacing(20)

        self.quick_scan = QuickScanCard()
        self.quick_scan.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        mid_row.addWidget(self.quick_scan, stretch=1)

        self.activity = RecentActivityCard()
        self.activity.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        mid_row.addWidget(self.activity, stretch=1)

        centre.addLayout(mid_row)

        # Stretch remaining vertical space
        centre.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        outer.addLayout(centre, stretch=1)

        # ── Right info panel ──
        self.info_panel = InfoPanelCard()
        outer.addWidget(self.info_panel)

        return container

    # ── Signal wiring ──────────────────────────────────────────────

    def _connect_signals(self) -> None:
        """Wire child-widget signals to the upload handler."""
        self.quick_scan.upload_requested.connect(self._handle_upload)

    # ── Upload handler ─────────────────────────────────────────────

    def _handle_upload(self) -> None:
        """Orchestrate the model upload pipeline and update the UI."""
        from services.model_upload_service import ModelUploadService

        service = ModelUploadService()
        record = service.process_upload(parent=self)

        if record is None:
            # User cancelled the dialog or file was invalid
            return

        # Update the right-side info panel with model metadata
        self.info_panel.update_model_info(record)

        # Enable the Scan button and show a success message
        self.quick_scan.enable_scan_button()
        self.quick_scan.show_success(record.filename)

        # Flash a success message in the bottom status bar
        self.status_bar.set_message("✔ Model uploaded successfully.")

    # ── Stat cards builder ─────────────────────────────────────────

    @staticmethod
    def _build_stat_cards() -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(16)

        cards_data = [
            ("🔬", "0", "Models Scanned", _T.accent),
            ("🛡️", "0", "Threats Detected", _T.danger),
            ("📊", "0%", "Risk Score", _T.warning),
            ("📄", "0", "Reports Generated", _T.info),
        ]

        for icon, value, label, color in cards_data:
            card = StatCard(icon, value, label, accent_color=color)
            card.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
            )
            row.addWidget(card)

        return row

