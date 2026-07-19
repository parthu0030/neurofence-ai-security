"""Bottom status bar widget for NeuroFence.

Displays application readiness, Python version,
placeholder memory usage, and the application version.
"""

from __future__ import annotations

import platform
import sys

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSpacerItem,
    QWidget,
)

from config.settings import AppConfig
from ui.styles import STATUS_BAR_STYLESHEET


class StatusBarWidget(QFrame):
    """Thin status strip anchored to the bottom of the window."""

    BAR_HEIGHT = 28

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("StatusBarFrame")
        self.setFixedHeight(self.BAR_HEIGHT)
        self.setStyleSheet(STATUS_BAR_STYLESHEET)

        self._build_layout()

    def _build_layout(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(24)

        # Ready indicator
        self._status_dot = QLabel("●")
        self._status_dot.setObjectName("StatusBarReady")
        layout.addWidget(self._status_dot)

        self._status_text = QLabel("Ready")
        self._status_text.setObjectName("StatusBarReady")
        layout.addWidget(self._status_text)

        layout.addWidget(self._divider())

        # Python version
        py_ver = f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        layout.addWidget(self._info_label(py_ver))

        layout.addWidget(self._divider())

        # Memory usage placeholder
        layout.addWidget(self._info_label("Memory: 124 MB"))

        layout.addWidget(self._divider())

        # Platform
        layout.addWidget(self._info_label(f"{platform.system()} {platform.machine()}"))

        # Push version to the right
        layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        layout.addWidget(self._info_label(f"NeuroFence v{AppConfig.VERSION}"))

    # ── Helpers ────────────────────────────────────────────────────

    @staticmethod
    def _info_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("StatusBarLabel")
        return lbl

    @staticmethod
    def _divider() -> QLabel:
        div = QLabel("|")
        div.setStyleSheet("color: #2a3550; font-size: 11px;")
        return div

    # ── Public API ────────────────────────────────────────────────

    def set_message(self, text: str, timeout_ms: int = 5_000) -> None:
        """Display *text* in the status bar, reverting after *timeout_ms*."""
        self._status_text.setText(text)
        self._status_text.setStyleSheet("color: #22c55e; font-size: 11px; font-weight: 600;")
        QTimer.singleShot(timeout_ms, self._reset_status)

    def _reset_status(self) -> None:
        """Restore the default 'Ready' status."""
        self._status_text.setText("Ready")
        self._status_text.setStyleSheet("")
        self._status_text.setObjectName("StatusBarReady")
        self._status_text.style().unpolish(self._status_text)
        self._status_text.style().polish(self._status_text)
