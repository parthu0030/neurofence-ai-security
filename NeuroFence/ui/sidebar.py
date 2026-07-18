"""Left sidebar navigation widget for NeuroFence.

Provides icon+label navigation buttons with hover effects
and an active-page highlight.  An "About" link is pinned
to the bottom of the sidebar.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from config.settings import NAV_ITEMS, NavItem
from ui.styles import SIDEBAR_STYLESHEET


class SidebarWidget(QFrame):
    """Collapsible-ready sidebar with navigation buttons."""

    # Emitted when the user clicks a navigation item.
    page_changed = pyqtSignal(str)

    SIDEBAR_WIDTH = 220

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("SidebarFrame")
        self.setFixedWidth(self.SIDEBAR_WIDTH)
        self.setStyleSheet(SIDEBAR_STYLESHEET)

        self._active_key: str = "dashboard"
        self._nav_buttons: dict[str, QPushButton] = {}

        self._build_layout()

    # ── Layout construction ────────────────────────────────────────

    def _build_layout(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(4)

        # Logo section
        layout.addLayout(self._build_logo_section())
        layout.addSpacing(24)

        # Navigation buttons
        for item in NAV_ITEMS:
            btn = self._make_nav_button(item)
            self._nav_buttons[item.page_key] = btn
            layout.addWidget(btn)

        # Push "About" to bottom
        layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # Separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #1e293b;")
        layout.addWidget(sep)

        # About button
        about_btn = QPushButton("  ℹ   About")
        about_btn.setObjectName("AboutButton")
        about_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(about_btn)

        # Apply initial active state
        self._refresh_active_states()

    def _build_logo_section(self) -> QVBoxLayout:
        """Construct the sidebar logo / branding block."""
        box = QVBoxLayout()
        box.setSpacing(2)

        shield_label = QLabel("🛡️")
        shield_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shield_label.setStyleSheet("font-size: 32px;")
        box.addWidget(shield_label)

        title = QLabel("NeuroFence")
        title.setObjectName("SidebarLogo")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        box.addWidget(title)

        sub = QLabel("AI Security Platform")
        sub.setObjectName("SidebarLogoSub")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        box.addWidget(sub)

        return box

    # ── Button helpers ─────────────────────────────────────────────

    def _make_nav_button(self, item: NavItem) -> QPushButton:
        btn = QPushButton(f"  {item.icon}   {item.label}")
        btn.setObjectName("NavButton")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.clicked.connect(lambda _checked, key=item.page_key: self._on_nav_click(key))
        return btn

    def _on_nav_click(self, page_key: str) -> None:
        if page_key == self._active_key:
            return
        self._active_key = page_key
        self._refresh_active_states()
        self.page_changed.emit(page_key)

    def _refresh_active_states(self) -> None:
        """Toggle object names so the stylesheet picks up the active state."""
        for key, btn in self._nav_buttons.items():
            if key == self._active_key:
                btn.setObjectName("NavButtonActive")
            else:
                btn.setObjectName("NavButton")
            # Force style re-evaluation
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            btn.update()
