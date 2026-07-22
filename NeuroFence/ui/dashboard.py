"""Main dashboard compositor for NeuroFence.

Assembles the sidebar, header, stat cards, quick-scan panel,
recent-activity table, right-side info panel, bottom status bar,
the Prompt Engine panel, and the Activation Tracking panel — all
navigable via the sidebar using a ``QStackedWidget``.
"""

from __future__ import annotations

import logging
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from config.settings import ThemeColors
from ui.cards import InfoPanelCard, QuickScanCard, RecentActivityCard, StatCard
from ui.header import HeaderWidget
from ui.prompt_panel import PromptPanel
from ui.activation_panel import ActivationPanel
from ui.sidebar import SidebarWidget
from ui.statusbar import StatusBarWidget

log = logging.getLogger(__name__)
_T = ThemeColors()


class DashboardWindow(QWidget):
    """Top-level widget compositing every dashboard component.

    This widget is set as the ``centralWidget`` of the ``QMainWindow``
    in ``app.py``.  It owns the sidebar, header, content area, and
    status bar and wires them together with layout managers.

    A ``QStackedWidget`` is used so the sidebar can swap between the
    main dashboard overview, the Prompt Engine page, and the
    Activation Tracking page.
    """

    # Map sidebar page_key → QStackedWidget index
    _PAGE_INDEX: dict[str, int] = {
        "dashboard": 0,
        "prompt_engine": 1,
        "activations": 2,
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # Activation tracker — initialised when a model is loaded
        self._activation_tracker = None

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

        # ── Right column: header + stacked content + status bar ──
        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(0)

        # Header
        self.header = HeaderWidget()
        right_col.addWidget(self.header)

        # ── Stacked content area ──
        self._stack = QStackedWidget()

        # Page 0 — Dashboard overview (wrapped in a scroll area)
        dash_scroll = QScrollArea()
        dash_scroll.setWidgetResizable(True)
        dash_scroll.setFrameShape(QFrame.Shape.NoFrame)
        dash_scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
        )
        dash_scroll.setWidget(self._build_content_area())
        self._stack.addWidget(dash_scroll)  # index 0

        # Page 1 — Prompt Engine
        self.prompt_panel = PromptPanel()
        self._stack.addWidget(self.prompt_panel)  # index 1

        # Page 2 — Activation Tracking
        self.activation_panel = ActivationPanel()
        self._stack.addWidget(self.activation_panel)  # index 2

        right_col.addWidget(self._stack, stretch=1)

        # Status bar
        self.status_bar = StatusBarWidget()
        right_col.addWidget(self.status_bar)

        root.addLayout(right_col, stretch=1)

    # ── Content area (dashboard overview) ──────────────────────────

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
        """Wire child-widget signals to the upload and scan handlers."""
        self.quick_scan.upload_requested.connect(self._handle_upload)
        self.quick_scan.scan_requested.connect(self._handle_scan)
        self.sidebar.page_changed.connect(self._on_page_changed)

        # Prompt execution → activation tracking pipeline
        self.prompt_panel.prompt_executed.connect(self._on_prompt_executed)

    # ── Sidebar navigation ─────────────────────────────────────────

    def _on_page_changed(self, page_key: str) -> None:
        """Switch the stacked widget to the requested page."""
        index = self._PAGE_INDEX.get(page_key)
        if index is not None:
            self._stack.setCurrentIndex(index)

    # ── Upload handler ─────────────────────────────────────────────

    def _handle_upload(self) -> None:
        """Orchestrate the model upload pipeline and update the UI."""
        from services.model_upload_service import ModelUploadService

        service = ModelUploadService()
        record = service.process_upload(parent=self)

        if record is None:
            # User cancelled the dialog or file was invalid
            return

        # Stash the latest record for the scan handler
        self._latest_record = record

        # Update the right-side info panel with model metadata
        self.info_panel.update_model_info(record)

        # Enable the Scan button and show a success message
        self.quick_scan.enable_scan_button()
        self.quick_scan.show_success(record.filename)

        # Flash a success message in the bottom status bar
        self.status_bar.set_message("✔ Model uploaded successfully.")

    # ── Scan / Load handler ────────────────────────────────────────

    def _handle_scan(self) -> None:
        """Load the uploaded model and display inspection results."""
        from database.database import DatabaseManager

        # Try the stashed record first, then fall back to the DB
        record = getattr(self, "_latest_record", None)
        if record is None:
            db = DatabaseManager()
            record = db.get_latest_model()

        if record is None:
            QMessageBox.warning(
                self,
                "No Model",
                "Please upload a model file before loading.",
            )
            return

        from ui.loading_dialog import LoadingDialog

        dialog = LoadingDialog(record, parent=self)
        dialog.model_loaded.connect(self._on_model_loaded)
        dialog.exec()

    def _on_model_loaded(self, result) -> None:
        """Handle a successful model load — update all UI panels."""
        # Update the inspection section in the info panel
        self.info_panel.update_inspection_info(result)

        # Update the quick scan card
        self.quick_scan.show_model_loaded()

        # Flash a success message in the bottom status bar
        self.status_bar.set_message("✔ Model loaded successfully — ready for analysis.")

        # Provide the model and tokenizer to the prompt panel
        model_id = getattr(self._latest_record, "id", 0) or 0
        self.prompt_panel.set_model(
            model=result.model_ref,
            tokenizer=result.tokenizer_ref,
            model_id=model_id,
        )

        # ── Register activation hooks ────────────────────────────────
        self._setup_activation_tracker(result.model_ref)

    # ── Activation tracking ────────────────────────────────────────

    def _setup_activation_tracker(self, model) -> None:
        """Create the activation tracker and register hooks on the model."""
        from services.activation_tracker_service import ActivationTrackerService

        # Remove old hooks if re-loading
        if self._activation_tracker is not None:
            self._activation_tracker.remove_hooks()

        self._activation_tracker = ActivationTrackerService()
        success = self._activation_tracker.register_hooks(model)

        if success:
            log.info(
                "Activation hooks registered on %d layers.",
                self._activation_tracker.layer_count,
            )
            self.status_bar.set_message(
                f"✔ Activation hooks registered on "
                f"{self._activation_tracker.layer_count} layers."
            )
        else:
            log.warning("No transformer layers found for activation tracking.")
            QMessageBox.information(
                self,
                "Activation Tracking",
                "No transformer layers were detected in this model.\n\n"
                "Activation tracking will be unavailable.",
            )

    def _on_prompt_executed(self, result) -> None:
        """Process activations after a successful prompt execution.

        This is triggered by the ``prompt_executed`` signal from the
        :class:`PromptPanel`.  The flow is:

        1. Compute activation summaries from the captured forward hooks.
        2. Update the Activation Tracking panel UI.
        3. Persist summaries to the ``activation_history`` table.
        """
        if result.status != "success":
            return

        if self._activation_tracker is None or not self._activation_tracker.has_hooks:
            log.warning("Activation tracker not available — skipping.")
            return

        try:
            summary = self._activation_tracker.process_activations()

            if summary is None or not summary.capture_successful:
                log.warning("Activation capture returned no data.")
                self.status_bar.set_message(
                    "⚠ Activation capture returned no data."
                )
                return

            # Update the Activation Tracking panel
            self.activation_panel.update_activation_data(summary)

            # Persist to SQLite
            self._save_activation_history(summary)

            # Update status bar
            self.status_bar.set_message(
                f"✔ Captured activations from {summary.layers_captured} layers "
                f"| Avg: {summary.average_activation:.6f} "
                f"| Peak: {summary.peak_activation:.4f}"
            )

            log.info(
                "Activation tracking complete — %d layers captured.",
                summary.layers_captured,
            )

        except Exception as exc:
            log.exception("Activation processing failed: %s", exc)
            self.status_bar.set_message("✖ Activation processing failed.")
            QMessageBox.warning(
                self,
                "Activation Error",
                f"Failed to process activations:\n\n{exc}",
            )

    def _save_activation_history(self, summary) -> None:
        """Persist activation summaries to the database."""
        try:
            from database.database import DatabaseManager
            from database.models import ActivationHistoryRecord

            db = DatabaseManager()
            prompt_id = db.get_latest_prompt_id()

            if prompt_id is None:
                log.warning("No prompt_history record found — skipping activation save.")
                return

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            records = [
                ActivationHistoryRecord(
                    prompt_id=prompt_id,
                    layer_number=la.layer_number,
                    mean=la.mean,
                    std=la.std,
                    minimum=la.min,
                    maximum=la.max,
                    norm=la.norm,
                    tensor_shape=la.tensor_shape,
                    created_at=now,
                )
                for la in summary.layers
            ]

            db.insert_activation_batch(records)
            log.info(
                "Saved %d activation records for prompt_id=%d.",
                len(records),
                prompt_id,
            )

        except Exception as exc:
            log.exception("Failed to save activation history: %s", exc)

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

    # ── Cleanup ────────────────────────────────────────────────────

    def closeEvent(self, event) -> None:
        """Remove activation hooks when the window closes."""
        if self._activation_tracker is not None:
            self._activation_tracker.remove_hooks()
            log.info("Activation hooks removed on window close.")
        super().closeEvent(event)
