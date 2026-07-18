"""Top header bar widget for NeuroFence.

Displays the application title, version, live status indicator,
current date-time, and a search bar (UI-only, no functionality).
"""

from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QSpacerItem,
    QWidget,
)

from config.settings import AppConfig
from ui.styles import HEADER_STYLESHEET


class HeaderWidget(QFrame):
    """Sticky top header with branding, status, datetime, and search."""

    HEADER_HEIGHT = 56

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("HeaderFrame")
        self.setFixedHeight(self.HEADER_HEIGHT)
        self.setStyleSheet(HEADER_STYLESHEET)

        self._datetime_label: QLabel | None = None
        self._build_layout()
        self._start_clock()

    # ── Layout ─────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(12)

        # ── Left cluster: logo + title + version ──
        logo = QLabel("🛡️")
        logo.setStyleSheet("font-size: 22px;")
        layout.addWidget(logo)

        title = QLabel(AppConfig.APP_TITLE)
        title.setObjectName("HeaderTitle")
        layout.addWidget(title)

        version = QLabel(f"v{AppConfig.VERSION}")
        version.setObjectName("HeaderVersion")
        layout.addWidget(version)

        layout.addSpacing(24)

        # ── Status indicator ──
        status_dot = QLabel("●")
        status_dot.setStyleSheet("color: #22c55e; font-size: 10px;")
        layout.addWidget(status_dot)

        status_text = QLabel("Ready")
        status_text.setObjectName("HeaderStatus")
        layout.addWidget(status_text)

        # ── Flexible spacer ──
        layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        # ── Search bar ──
        search = QLineEdit()
        search.setObjectName("SearchBar")
        search.setPlaceholderText("🔍  Search models, scans, reports…")
        search.setFixedWidth(280)
        layout.addWidget(search)

        layout.addSpacing(16)

        # ── Date & time ──
        self._datetime_label = QLabel()
        self._datetime_label.setObjectName("HeaderDateTime")
        layout.addWidget(self._datetime_label)

        self._update_clock()

    # ── Live clock ─────────────────────────────────────────────────

    def _start_clock(self) -> None:
        timer = QTimer(self)
        timer.timeout.connect(self._update_clock)
        timer.start(1_000)  # Update every second

    def _update_clock(self) -> None:
        now = datetime.now().strftime("%b %d, %Y  •  %I:%M:%S %p")
        if self._datetime_label is not None:
            self._datetime_label.setText(now)
