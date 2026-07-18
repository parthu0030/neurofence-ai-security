"""Dashboard card widgets for NeuroFence.

Contains four reusable card components:
- StatCard          — single metric (icon + value + label)
- QuickScanCard     — model upload / drag-drop area
- RecentActivityCard — placeholder activity table
- InfoPanelCard     — right-side project & system information
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config.settings import ThemeColors
from ui.styles import (
    ACTIVITY_STYLESHEET,
    CARD_STYLESHEET,
    INFO_PANEL_STYLESHEET,
    QUICK_SCAN_STYLESHEET,
)

_T = ThemeColors()


# ═══════════════════════════════════════════════════════════════════════════
#  Stat Card
# ═══════════════════════════════════════════════════════════════════════════


class StatCard(QFrame):
    """A compact statistics card with icon, numeric value, and label."""

    def __init__(
        self,
        icon: str,
        value: str,
        label: str,
        accent_color: str = _T.accent,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.setStyleSheet(CARD_STYLESHEET)
        self.setMinimumHeight(110)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(4)

        # Icon row
        icon_row = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setObjectName("StatCardIcon")
        icon_label.setStyleSheet(f"color: {accent_color};")
        icon_row.addWidget(icon_label)
        icon_row.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )
        layout.addLayout(icon_row)

        layout.addSpacing(4)

        # Value
        val = QLabel(value)
        val.setObjectName("StatCardValue")
        layout.addWidget(val)

        # Label
        lbl = QLabel(label)
        lbl.setObjectName("StatCardLabel")
        layout.addWidget(lbl)


# ═══════════════════════════════════════════════════════════════════════════
#  Quick Scan Card
# ═══════════════════════════════════════════════════════════════════════════


class QuickScanCard(QFrame):
    """Large card with upload button, drag-drop zone, and disabled Scan button."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("QuickScanCard")
        self.setStyleSheet(QUICK_SCAN_STYLESHEET)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Title
        title = QLabel("⚡  Quick Scan")
        title.setObjectName("QuickScanTitle")
        layout.addWidget(title)

        # Upload button (centred)
        upload_btn = QPushButton("📤  Upload Model")
        upload_btn.setObjectName("UploadBtn")
        upload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        upload_btn.setFixedHeight(48)
        layout.addWidget(upload_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Drag & Drop zone
        drop_zone = QFrame()
        drop_zone.setObjectName("DropZone")
        drop_zone.setMinimumHeight(90)
        drop_layout = QVBoxLayout(drop_zone)
        drop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        drop_icon = QLabel("📂")
        drop_icon.setStyleSheet("font-size: 28px;")
        drop_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_layout.addWidget(drop_icon)

        drop_text = QLabel("Drag & Drop Model File Here")
        drop_text.setObjectName("DropZoneText")
        drop_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_layout.addWidget(drop_text)

        layout.addWidget(drop_zone)

        # Supported formats row
        fmt_label = QLabel("Supported Formats:")
        fmt_label.setObjectName("FormatsLabel")
        layout.addWidget(fmt_label)

        fmt_row = QHBoxLayout()
        fmt_row.setSpacing(8)
        for ext in (".safetensors", ".bin", ".pt"):
            badge = QLabel(ext)
            badge.setObjectName("FormatBadge")
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fmt_row.addWidget(badge)
        fmt_row.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )
        layout.addLayout(fmt_row)

        layout.addSpacing(4)

        # Scan button (disabled — no backend yet)
        scan_btn = QPushButton("🔍  Scan Model")
        scan_btn.setObjectName("ScanBtn")
        scan_btn.setEnabled(False)
        scan_btn.setFixedHeight(44)
        layout.addWidget(scan_btn, alignment=Qt.AlignmentFlag.AlignCenter)


# ═══════════════════════════════════════════════════════════════════════════
#  Recent Activity Card
# ═══════════════════════════════════════════════════════════════════════════

# Placeholder data for the activity table.
_PLACEHOLDER_ROWS: list[tuple[str, str, str, str]] = [
    ("Jul 18, 02:14 PM", "tinyllama-1.1b.safetensors", "✅ Clean", "Low"),
    ("Jul 17, 11:45 AM", "phi-2-merged.bin", "⚠️ Suspicious", "Medium"),
    ("Jul 16, 09:30 AM", "gemma-2b.pt", "✅ Clean", "Low"),
    ("Jul 15, 04:20 PM", "llama-7b-q4.bin", "❌ Threat", "Critical"),
    ("Jul 14, 10:05 AM", "custom-lora.safetensors", "✅ Clean", "Low"),
]


class RecentActivityCard(QFrame):
    """Table card showing recent model scan activity."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ActivityCard")
        self.setStyleSheet(ACTIVITY_STYLESHEET)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        title = QLabel("📋  Recent Activity")
        title.setObjectName("ActivityTitle")
        layout.addWidget(title)

        self._table = self._build_table()
        layout.addWidget(self._table)

    @staticmethod
    def _build_table() -> QTableWidget:
        headers = ["Time", "Model", "Status", "Risk"]
        table = QTableWidget(len(_PLACEHOLDER_ROWS), len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setShowGrid(False)
        table.setAlternatingRowColors(False)

        # Stretch columns proportionally
        h_header = table.horizontalHeader()
        h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        # Populate rows
        risk_colors = {
            "Low": _T.success,
            "Medium": _T.warning,
            "Critical": _T.danger,
        }
        for row_idx, (time, model, status, risk) in enumerate(_PLACEHOLDER_ROWS):
            for col_idx, text in enumerate((time, model, status, risk)):
                item = QTableWidgetItem(text)
                item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                if col_idx == 3:  # Risk column — colour-code
                    from PyQt6.QtGui import QColor
                    item.setForeground(QColor(risk_colors.get(risk, _T.text_primary)))
                table.setItem(row_idx, col_idx, item)

        table.setMinimumHeight(200)
        return table


# ═══════════════════════════════════════════════════════════════════════════
#  Info Panel (right side)
# ═══════════════════════════════════════════════════════════════════════════


class InfoPanelCard(QFrame):
    """Right-side panel showing project info, supported models, and system status."""

    PANEL_WIDTH = 260

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("InfoPanel")
        self.setStyleSheet(INFO_PANEL_STYLESHEET)
        self.setFixedWidth(self.PANEL_WIDTH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # ── Project Information ──
        layout.addWidget(self._section_title("PROJECT INFORMATION"))
        layout.addLayout(self._kv_row("Application", "NeuroFence AI Security"))
        layout.addLayout(self._kv_row("Version", "v1.0"))
        layout.addLayout(self._kv_row("License", "Research / Academic"))

        layout.addWidget(self._separator())

        # ── Supported Models ──
        layout.addWidget(self._section_title("SUPPORTED MODELS"))
        models_row = QHBoxLayout()
        models_row.setSpacing(6)
        for model_name in ("TinyLlama", "Gemma", "Phi", "Llama"):
            badge = QLabel(model_name)
            badge.setObjectName("ModelBadge")
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            models_row.addWidget(badge)
        layout.addLayout(models_row)

        layout.addWidget(self._separator())

        # ── System Status ──
        layout.addWidget(self._section_title("SYSTEM STATUS"))
        layout.addLayout(self._status_row("System", "Ready", _T.success))
        layout.addLayout(self._status_row("GPU", "Not Connected", _T.text_muted))
        layout.addLayout(self._kv_row("Last Scan", "Never"))

        # Push remaining space down
        layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

    # ── Helper builders ────────────────────────────────────────────

    @staticmethod
    def _section_title(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("InfoSectionTitle")
        return lbl

    @staticmethod
    def _kv_row(key: str, value: str) -> QHBoxLayout:
        row = QHBoxLayout()
        k = QLabel(key)
        k.setObjectName("InfoKey")
        v = QLabel(value)
        v.setObjectName("InfoValue")
        v.setAlignment(Qt.AlignmentFlag.AlignRight)
        row.addWidget(k)
        row.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )
        row.addWidget(v)
        return row

    @staticmethod
    def _status_row(key: str, value: str, color: str) -> QHBoxLayout:
        row = QHBoxLayout()
        k = QLabel(key)
        k.setObjectName("InfoKey")
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {color}; font-size: 8px;")
        v = QLabel(value)
        v.setObjectName("InfoValue")
        v.setStyleSheet(f"color: {color};")
        row.addWidget(k)
        row.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )
        row.addWidget(dot)
        row.addSpacing(4)
        row.addWidget(v)
        return row

    @staticmethod
    def _separator() -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {_T.border};")
        sep.setFixedHeight(1)
        return sep
