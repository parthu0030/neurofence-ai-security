"""Dashboard card widgets for NeuroFence.

Contains four reusable card components:
- StatCard          — single metric (icon + value + label)
- QuickScanCard     — model upload / drag-drop area
- RecentActivityCard — placeholder activity table
- InfoPanelCard     — right-side project & system information
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
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
    """Large card with upload button, drag-drop zone, and Scan button."""

    # Emitted when the upload button is clicked.
    upload_requested = pyqtSignal()
    # Emitted when the scan button is clicked (after a model is uploaded).
    scan_requested = pyqtSignal()

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
        self.upload_btn = QPushButton("📤  Upload Model")
        self.upload_btn.setObjectName("UploadBtn")
        self.upload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.upload_btn.setFixedHeight(48)
        self.upload_btn.clicked.connect(self.upload_requested.emit)
        layout.addWidget(self.upload_btn, alignment=Qt.AlignmentFlag.AlignCenter)

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

        # Success label (hidden by default)
        self._success_label = QLabel("")
        self._success_label.setObjectName("SuccessLabel")
        self._success_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._success_label.hide()
        layout.addWidget(self._success_label)

        layout.addSpacing(4)

        # Scan / Load Model button (disabled until upload)
        self.scan_btn = QPushButton("🔍  Load Model")
        self.scan_btn.setObjectName("ScanBtn")
        self.scan_btn.setEnabled(False)
        self.scan_btn.setFixedHeight(44)
        self.scan_btn.clicked.connect(self.scan_requested.emit)
        layout.addWidget(self.scan_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    # ── Public API ────────────────────────────────────────────────────

    def enable_scan_button(self) -> None:
        """Enable the Scan button after a valid model is uploaded."""
        self.scan_btn.setEnabled(True)
        self.scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        # Force style re-evaluation for the enabled state
        self.scan_btn.style().unpolish(self.scan_btn)
        self.scan_btn.style().polish(self.scan_btn)
        self.scan_btn.update()

    def show_success(self, filename: str) -> None:
        """Display a success message below the format badges."""
        self._success_label.setText("✔ Model uploaded successfully.")
        self._success_label.show()

    def show_model_loaded(self) -> None:
        """Update the button and label after a successful model load."""
        self._success_label.setText("✔ Model loaded & inspected successfully.")
        self._success_label.show()
        self.scan_btn.setText("✔  Model Ready")
        self.scan_btn.setEnabled(False)
        self.scan_btn.style().unpolish(self.scan_btn)
        self.scan_btn.style().polish(self.scan_btn)
        self.scan_btn.update()


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
    """Table card showing recent model scan activity loaded from SQLite."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ActivityCard")
        self.setStyleSheet(ACTIVITY_STYLESHEET)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        header_row = QHBoxLayout()
        title = QLabel("📋  Recent Scans")
        title.setObjectName("ActivityTitle")
        header_row.addWidget(title)

        header_row.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        layout.addLayout(header_row)

        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["Time", "Model", "Status", "Score"])
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setShowGrid(False)
        self._table.setAlternatingRowColors(False)
        self._table.setMinimumHeight(180)

        h_header = self._table.horizontalHeader()
        h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self._table)
        self.refresh_scans()

    def refresh_scans(self) -> None:
        """Fetch latest scans from database and update table rows."""
        from services.scan_history_service import ScanHistoryService
        from PyQt6.QtGui import QColor

        service = ScanHistoryService()
        scans = service.get_all_scans()[:5]  # Top 5 recent scans

        if not scans:
            # Fallback to placeholder rows if DB has no scans yet
            rows_data = _PLACEHOLDER_ROWS
            self._table.setRowCount(len(rows_data))
            for r_idx, (t, m, s, r) in enumerate(rows_data):
                for c_idx, val in enumerate((t, m, s, r)):
                    item = QTableWidgetItem(val)
                    item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                    self._table.setItem(r_idx, c_idx, item)
            return

        self._table.setRowCount(len(scans))
        risk_colors = {
            "Clean": _T.success,
            "Low Risk": _T.success,
            "Medium Risk": _T.warning,
            "High Risk": _T.danger,
            "Critical Risk": _T.danger,
        }

        for r_idx, scan in enumerate(scans):
            t_str = str(scan.get("scan_date", ""))[:16]
            m_str = str(scan.get("filename", "Unknown"))
            st_str = str(scan.get("overall_status", "Clean"))
            score = float(scan.get("security_score", 0.0))

            items = [
                QTableWidgetItem(t_str),
                QTableWidgetItem(m_str),
                QTableWidgetItem(st_str),
                QTableWidgetItem(f"{score:.1f}"),
            ]

            items[2].setForeground(QColor(risk_colors.get(st_str, _T.text_primary)))
            items[3].setForeground(QColor(_T.success if score >= 80 else (_T.warning if score >= 60 else _T.danger)))

            for c_idx, item in enumerate(items):
                item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                self._table.setItem(r_idx, c_idx, item)


# ═══════════════════════════════════════════════════════════════════════════
#  Scan Highlights & Quick Compare Card
# ═══════════════════════════════════════════════════════════════════════════


class ScanHighlightsCard(QFrame):
    """Card displaying Latest Scan, Best Scan, Worst Scan, and Quick Compare trigger."""

    quick_compare_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ActivityCard")
        self.setStyleSheet(ACTIVITY_STYLESHEET)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        title = QLabel("🏆  Scan Highlights & Quick Compare")
        title.setObjectName("ActivityTitle")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(10)

        # Labels
        grid.addWidget(self._make_header("Metric"), 0, 0)
        grid.addWidget(self._make_header("Model"), 0, 1)
        grid.addWidget(self._make_header("Score"), 0, 2)

        self.latest_model = QLabel("—")
        self.latest_score = QLabel("—")
        self.best_model = QLabel("—")
        self.best_score = QLabel("—")
        self.worst_model = QLabel("—")
        self.worst_score = QLabel("—")

        grid.addWidget(QLabel("🕒 Latest Scan:"), 1, 0)
        grid.addWidget(self.latest_model, 1, 1)
        grid.addWidget(self.latest_score, 1, 2)

        grid.addWidget(QLabel("🌟 Best Scan:"), 2, 0)
        grid.addWidget(self.best_model, 2, 1)
        grid.addWidget(self.best_score, 2, 2)

        grid.addWidget(QLabel("⚠️ Worst Scan:"), 3, 0)
        grid.addWidget(self.worst_model, 3, 1)
        grid.addWidget(self.worst_score, 3, 2)

        layout.addLayout(grid)

        # Quick Compare Button
        self.compare_btn = QPushButton("⚔️  Quick Compare Scans")
        self.compare_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.compare_btn.setStyleSheet(f"background-color: {_T.accent}; color: #ffffff; border: none; border-radius: 8px; padding: 10px; font-weight: 700; margin-top: 6px;")
        self.compare_btn.clicked.connect(self.quick_compare_requested.emit)
        layout.addWidget(self.compare_btn)

        self.refresh_highlights()

    @staticmethod
    def _make_header(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {_T.text_muted}; font-size: 11px; font-weight: 700; text-transform: uppercase;")
        return lbl

    def refresh_highlights(self) -> None:
        """Fetch scans and update Latest, Best, and Worst cards."""
        from services.scan_history_service import ScanHistoryService

        service = ScanHistoryService()
        scans = service.get_all_scans()

        if not scans:
            self.latest_model.setText("No Scans")
            self.latest_score.setText("—")
            self.best_model.setText("No Scans")
            self.best_score.setText("—")
            self.worst_model.setText("No Scans")
            self.worst_score.setText("—")
            return

        # Latest scan (first item as get_all_scans orders newest first)
        latest = scans[0]
        self.latest_model.setText(str(latest.get("filename", "Unknown")))
        self.latest_score.setText(f"{float(latest.get('security_score', 0)):.1f}")
        self.latest_score.setStyleSheet(f"color: {_T.accent_light}; font-weight: 700;")

        # Best scan (highest score)
        best = max(scans, key=lambda s: float(s.get("security_score", 0)))
        self.best_model.setText(str(best.get("filename", "Unknown")))
        self.best_score.setText(f"{float(best.get('security_score', 0)):.1f}")
        self.best_score.setStyleSheet(f"color: {_T.success}; font-weight: 700;")

        # Worst scan (lowest score)
        worst = min(scans, key=lambda s: float(s.get("security_score", 0)))
        self.worst_model.setText(str(worst.get("filename", "Unknown")))
        self.worst_score.setText(f"{float(worst.get('security_score', 0)):.1f}")
        self.worst_score.setStyleSheet(f"color: {_T.danger}; font-weight: 700;")


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

        # ── Model Information (populated after upload) ──
        layout.addWidget(self._section_title("MODEL INFORMATION"))

        self._model_info_labels: dict[str, QLabel] = {}
        for key in (
            "Model Name",
            "Filename",
            "Extension",
            "Size",
            "Created",
            "Modified",
            "Path",
        ):
            row, val_label = self._model_info_row(key)
            self._model_info_labels[key] = val_label
            layout.addLayout(row)

        # SHA-256 gets its own monospace label
        sha_header = QLabel("SHA-256")
        sha_header.setObjectName("InfoKey")
        layout.addWidget(sha_header)

        self._sha_label = QLabel("—")
        self._sha_label.setObjectName("Sha256Value")
        self._sha_label.setWordWrap(True)
        layout.addWidget(self._sha_label)

        layout.addWidget(self._separator())

        # ── Model Inspection (populated after loading) ──
        layout.addWidget(self._section_title("MODEL INSPECTION"))

        self._inspection_labels: dict[str, QLabel] = {}
        for key in (
            "Model Loaded",
            "Architecture",
            "Tokenizer Loaded",
            "Device",
            "Model Status",
            "Layers",
            "Hidden Size",
            "Vocab Size",
            "Context Length",
            "Attention Heads",
            "Parameters",
            "Dtype",
        ):
            row, val_label = self._model_info_row(key)
            self._inspection_labels[key] = val_label
            layout.addLayout(row)

        layout.addWidget(self._separator())

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
        self._system_status_row_layout, self._system_status_label = self._status_row_with_ref(
            "System", "Ready", _T.success
        )
        layout.addLayout(self._system_status_row_layout)
        self._gpu_status_row_layout, self._gpu_status_label = self._status_row_with_ref(
            "GPU", "Not Connected", _T.text_muted
        )
        layout.addLayout(self._gpu_status_row_layout)
        layout.addLayout(self._kv_row("Last Scan", "Never"))

        # Push remaining space down
        layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

    # ── Public API ────────────────────────────────────────────────

    def update_model_info(self, record) -> None:
        """Populate the MODEL INFORMATION section from a ModelRecord."""
        from utils.file_metadata import _humanize_size, _derive_model_name

        self._model_info_labels["Model Name"].setText(
            _derive_model_name(record.filename)
        )
        self._model_info_labels["Filename"].setText(record.filename)
        self._model_info_labels["Extension"].setText(record.extension)
        self._model_info_labels["Size"].setText(_humanize_size(record.size))
        self._model_info_labels["Created"].setText(record.created_at)
        self._model_info_labels["Modified"].setText(record.modified_at)
        self._model_info_labels["Path"].setText(record.filepath)
        self._model_info_labels["Path"].setToolTip(record.filepath)

        self._sha_label.setText(record.sha256)
        self._sha_label.setToolTip(record.sha256)

    def update_inspection_info(self, result) -> None:
        """Populate the MODEL INSPECTION section from a ModelInspectionResult."""
        yes_style = f"color: {_T.success}; font-size: 11px; font-weight: 600;"
        no_style = f"color: {_T.danger}; font-size: 11px; font-weight: 600;"

        # Model Loaded
        lbl = self._inspection_labels["Model Loaded"]
        lbl.setText("YES" if result.model_loaded else "NO")
        lbl.setStyleSheet(yes_style if result.model_loaded else no_style)

        # Architecture
        self._inspection_labels["Architecture"].setText(result.architecture)

        # Tokenizer Loaded
        lbl = self._inspection_labels["Tokenizer Loaded"]
        lbl.setText("YES" if result.tokenizer_loaded else "NO")
        lbl.setStyleSheet(yes_style if result.tokenizer_loaded else no_style)

        # Device
        self._inspection_labels["Device"].setText(result.device)

        # Model Status
        status_lbl = self._inspection_labels["Model Status"]
        status_lbl.setText("Ready" if result.model_loaded else "Not Loaded")
        status_lbl.setStyleSheet(yes_style if result.model_loaded else no_style)

        # Numeric fields
        self._inspection_labels["Layers"].setText(str(result.layers))
        self._inspection_labels["Hidden Size"].setText(f"{result.hidden_size:,}")
        self._inspection_labels["Vocab Size"].setText(f"{result.vocab_size:,}")
        self._inspection_labels["Context Length"].setText(f"{result.context_length:,}")
        self._inspection_labels["Attention Heads"].setText(str(result.attention_heads))

        # Parameter count
        if result.parameter_count is not None:
            param_str = self._humanize_params(result.parameter_count)
            self._inspection_labels["Parameters"].setText(param_str)
        else:
            self._inspection_labels["Parameters"].setText("—")

        # Dtype
        self._inspection_labels["Dtype"].setText(result.dtype)

        # Update system status section
        self._gpu_status_label.setText(result.device)
        if result.device in ("CUDA", "MPS"):
            self._gpu_status_label.setStyleSheet(f"color: {_T.success}; font-size: 12px; font-weight: 500;")

    @staticmethod
    def _humanize_params(count: int) -> str:
        """Convert a parameter count to a human-readable string."""
        if count >= 1_000_000_000:
            return f"{count / 1_000_000_000:.2f}B"
        if count >= 1_000_000:
            return f"{count / 1_000_000:.2f}M"
        if count >= 1_000:
            return f"{count / 1_000:.1f}K"
        return str(count)

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
    def _model_info_row(key: str) -> tuple[QHBoxLayout, QLabel]:
        """Build a key-value row and return both the layout and the value label."""
        row = QHBoxLayout()
        k = QLabel(key)
        k.setObjectName("InfoKey")
        v = QLabel("—")
        v.setObjectName("ModelInfoValue")
        v.setAlignment(Qt.AlignmentFlag.AlignRight)
        v.setWordWrap(True)
        row.addWidget(k)
        row.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )
        row.addWidget(v)
        return row, v

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
    def _status_row_with_ref(
        key: str, value: str, color: str
    ) -> tuple[QHBoxLayout, QLabel]:
        """Like _status_row but also returns a reference to the value label."""
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
        return row, v

    @staticmethod
    def _separator() -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {_T.border};")
        sep.setFixedHeight(1)
        return sep

