"""Prompt Engine panel for NeuroFence.

Full-page widget providing:
- Category and prompt selection combo boxes
- Multiline prompt editor with character counter
- Generation parameter sliders
- Run Prompt button with threaded inference
- Response display with statistics grid
- Prompt history table

This widget communicates with the business layer through
:class:`PromptExecutionService` and never touches the database
directly.
"""

from __future__ import annotations

import logging
from datetime import datetime

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSpacerItem,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config.prompt_categories import CATEGORY_NAMES, PROMPT_CATEGORIES
from config.settings import ThemeColors
from ui.styles import PROMPT_PANEL_STYLESHEET

log = logging.getLogger(__name__)
_T = ThemeColors()

_MAX_PROMPT_CHARS = 2048


# ═══════════════════════════════════════════════════════════════════════════
#  Background inference worker
# ═══════════════════════════════════════════════════════════════════════════


class _InferenceWorker(QThread):
    """Runs prompt execution off the main thread."""

    finished = pyqtSignal(object)  # PromptExecutionResult
    error = pyqtSignal(str)

    def __init__(
        self,
        prompt: str,
        model,
        tokenizer,
        category: str,
        model_id: int,
        params,
        parent: QThread | None = None,
    ) -> None:
        super().__init__(parent)
        self._prompt = prompt
        self._model = model
        self._tokenizer = tokenizer
        self._category = category
        self._model_id = model_id
        self._params = params

    def run(self) -> None:
        try:
            from services.prompt_execution_service import PromptExecutionService

            service = PromptExecutionService()
            result = service.execute(
                prompt=self._prompt,
                model=self._model,
                tokenizer=self._tokenizer,
                category=self._category,
                model_id=self._model_id,
                params=self._params,
            )
            self.finished.emit(result)
        except Exception as exc:
            log.exception("Inference worker failed.")
            self.error.emit(str(exc))


# ═══════════════════════════════════════════════════════════════════════════
#  Prompt Panel
# ═══════════════════════════════════════════════════════════════════════════


class PromptPanel(QWidget):
    """Full-page Prompt Engine widget.

    Composed of three stacked cards:
    1. Prompt Input  — category/prompt selectors, editor, params, run button
    2. Response       — generated text + statistics
    3. History        — table of past executions
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("PromptPanelContainer")
        self.setStyleSheet(PROMPT_PANEL_STYLESHEET)

        # Live model references — set externally after a model is loaded
        self._model = None
        self._tokenizer = None
        self._model_id: int = 0
        self._worker: _InferenceWorker | None = None

        self._build_ui()
        self._connect_signals()

    # ── Public API ───────────────────────────────────────────────────

    def set_model(self, model, tokenizer, model_id: int = 0) -> None:
        """Provide the loaded model and tokenizer for inference."""
        self._model = model
        self._tokenizer = tokenizer
        self._model_id = model_id
        self._update_run_button_state()

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
        page_title = QLabel("💬  Prompt Execution Engine")
        page_title.setStyleSheet(
            f"color: {_T.text_primary}; font-size: 20px; font-weight: 700;"
        )
        layout.addWidget(page_title)

        page_sub = QLabel(
            "Execute prompts against the loaded model and analyse responses."
        )
        page_sub.setStyleSheet(
            f"color: {_T.text_secondary}; font-size: 13px;"
        )
        layout.addWidget(page_sub)

        # ── Card 1: Prompt Input ──────────────────────────────────────
        layout.addWidget(self._build_input_card())

        # ── Card 2: Response & Stats ──────────────────────────────────
        layout.addWidget(self._build_response_card())

        # ── Card 3: History ───────────────────────────────────────────
        layout.addWidget(self._build_history_card())

        # Stretch bottom
        layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        scroll.setWidget(container)
        outer.addWidget(scroll)

    # ── Card 1: Prompt Input ─────────────────────────────────────────

    def _build_input_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("PromptInputCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Title
        title = QLabel("📝  Prompt Input")
        title.setObjectName("PromptSectionTitle")
        layout.addWidget(title)

        # ── Category + Prompt selectors (side by side) ──
        sel_row = QHBoxLayout()
        sel_row.setSpacing(12)

        # Category combo
        cat_col = QVBoxLayout()
        cat_label = QLabel("Category")
        cat_label.setObjectName("SliderLabel")
        cat_col.addWidget(cat_label)
        self._category_combo = QComboBox()
        self._category_combo.setObjectName("CategoryCombo")
        self._category_combo.addItems(CATEGORY_NAMES)
        self._category_combo.addItem("Custom")
        cat_col.addWidget(self._category_combo)
        sel_row.addLayout(cat_col)

        # Prompt combo
        prompt_col = QVBoxLayout()
        prompt_label = QLabel("Predefined Prompt")
        prompt_label.setObjectName("SliderLabel")
        prompt_col.addWidget(prompt_label)
        self._prompt_combo = QComboBox()
        self._prompt_combo.setObjectName("PromptCombo")
        self._prompt_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        prompt_col.addWidget(self._prompt_combo)
        sel_row.addLayout(prompt_col, stretch=1)

        layout.addLayout(sel_row)

        # Populate initial prompts
        self._populate_prompts()

        # ── Multiline editor ──
        self._editor = QPlainTextEdit()
        self._editor.setObjectName("PromptEditor")
        self._editor.setPlaceholderText("Enter your prompt here…")
        self._editor.setMinimumHeight(100)
        self._editor.setMaximumHeight(160)
        layout.addWidget(self._editor)

        # Character counter
        self._char_counter = QLabel(f"0 / {_MAX_PROMPT_CHARS}")
        self._char_counter.setObjectName("CharCounter")
        self._char_counter.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self._char_counter)

        # ── Generation parameters ──
        params_title = QLabel("⚙  Generation Parameters")
        params_title.setObjectName("PromptSectionTitle")
        layout.addWidget(params_title)

        params_grid = QGridLayout()
        params_grid.setSpacing(12)

        # Temperature — 0.0 to 2.0, stored as int 0–20 (divide by 10)
        self._temp_slider, self._temp_value = self._make_slider(
            "Temperature", 0, 20, 7, params_grid, 0,
            fmt=lambda v: f"{v / 10:.1f}",
        )

        # Top-p — 0.0 to 1.0, stored as int 0–20 (divide by 20)
        self._top_p_slider, self._top_p_value = self._make_slider(
            "Top-p", 0, 20, 18, params_grid, 1,
            fmt=lambda v: f"{v / 20:.2f}",
        )

        # Top-k — 0 to 100
        self._top_k_slider, self._top_k_value = self._make_slider(
            "Top-k", 0, 100, 50, params_grid, 2,
            fmt=lambda v: str(v),
        )

        # Max Tokens — 16 to 512, step 16
        self._max_tok_slider, self._max_tok_value = self._make_slider(
            "Max Tokens", 1, 32, 8, params_grid, 3,
            fmt=lambda v: str(v * 16),
        )

        layout.addLayout(params_grid)

        # ── Run button row ──
        run_row = QHBoxLayout()
        run_row.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        self._running_label = QLabel("")
        self._running_label.setObjectName("RunningLabel")
        self._running_label.hide()
        run_row.addWidget(self._running_label)

        self._run_btn = QPushButton("▶  Run Prompt")
        self._run_btn.setObjectName("RunPromptBtn")
        self._run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._run_btn.setFixedHeight(48)
        self._run_btn.setMinimumWidth(200)
        self._run_btn.setEnabled(False)
        run_row.addWidget(self._run_btn)

        run_row.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        layout.addLayout(run_row)

        return card

    # ── Card 2: Response & Stats ─────────────────────────────────────

    def _build_response_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("ResponseCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("📤  Generated Response")
        title.setObjectName("PromptSectionTitle")
        layout.addWidget(title)

        # Response display
        self._response_display = QPlainTextEdit()
        self._response_display.setObjectName("ResponseDisplay")
        self._response_display.setReadOnly(True)
        self._response_display.setPlaceholderText(
            "Generated response will appear here after running a prompt…"
        )
        self._response_display.setMinimumHeight(120)
        self._response_display.setMaximumHeight(250)
        layout.addWidget(self._response_display)

        # ── Statistics grid ──
        stats_title = QLabel("📊  Response Statistics")
        stats_title.setObjectName("PromptSectionTitle")
        layout.addWidget(stats_title)

        stats_grid = QGridLayout()
        stats_grid.setSpacing(10)

        self._stat_labels: dict[str, QLabel] = {}

        stat_defs = [
            ("Input Tokens", 0, 0),
            ("Output Tokens", 0, 1),
            ("Characters", 0, 2),
            ("Inference Time", 1, 0),
            ("Avg Tokens/s", 1, 1),
            ("Status", 1, 2),
        ]

        for label_text, row, col in stat_defs:
            box = QFrame()
            box.setObjectName("StatBox")
            box_layout = QVBoxLayout(box)
            box_layout.setContentsMargins(14, 10, 14, 10)
            box_layout.setSpacing(4)

            lbl = QLabel(label_text)
            lbl.setObjectName("StatLabel")
            box_layout.addWidget(lbl)

            val = QLabel("—")
            val.setObjectName("StatValue")
            self._stat_labels[label_text] = val
            box_layout.addWidget(val)

            stats_grid.addWidget(box, row, col)

        layout.addLayout(stats_grid)

        return card

    # ── Card 3: History ──────────────────────────────────────────────

    def _build_history_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("HistoryCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("📋  Prompt History")
        title.setObjectName("PromptSectionTitle")
        layout.addWidget(title)

        headers = ["Time", "Category", "Prompt", "Response", "Time (s)"]
        self._history_table = QTableWidget(0, len(headers))
        self._history_table.setHorizontalHeaderLabels(headers)
        self._history_table.verticalHeader().setVisible(False)
        self._history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._history_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._history_table.setShowGrid(False)
        self._history_table.setAlternatingRowColors(False)
        self._history_table.setMinimumHeight(180)

        h_header = self._history_table.horizontalHeader()
        h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        h_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        h_header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self._history_table)

        # Load existing history
        self._refresh_history()

        return card

    # ── Signal wiring ────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        self._category_combo.currentIndexChanged.connect(self._on_category_changed)
        self._prompt_combo.currentIndexChanged.connect(self._on_prompt_selected)
        self._editor.textChanged.connect(self._on_text_changed)
        self._run_btn.clicked.connect(self._on_run_clicked)

        # Slider value updates
        self._temp_slider.valueChanged.connect(
            lambda v: self._temp_value.setText(f"{v / 10:.1f}")
        )
        self._top_p_slider.valueChanged.connect(
            lambda v: self._top_p_value.setText(f"{v / 20:.2f}")
        )
        self._top_k_slider.valueChanged.connect(
            lambda v: self._top_k_value.setText(str(v))
        )
        self._max_tok_slider.valueChanged.connect(
            lambda v: self._max_tok_value.setText(str(v * 16))
        )

    # ── Slot handlers ────────────────────────────────────────────────

    def _on_category_changed(self, _index: int) -> None:
        self._populate_prompts()

    def _populate_prompts(self) -> None:
        """Fill the prompt combo based on the selected category."""
        category = self._category_combo.currentText()
        self._prompt_combo.blockSignals(True)
        self._prompt_combo.clear()

        if category == "Custom":
            self._prompt_combo.addItem("(enter custom prompt below)")
            self._prompt_combo.setEnabled(False)
        else:
            prompts = PROMPT_CATEGORIES.get(category, [])
            for p in prompts:
                # Truncate long prompts for the combo display
                display = p[:80] + "…" if len(p) > 80 else p
                self._prompt_combo.addItem(display, userData=p)
            self._prompt_combo.setEnabled(True)

        self._prompt_combo.blockSignals(False)

        # Auto-select first prompt
        if self._prompt_combo.count() > 0:
            self._on_prompt_selected(0)

    def _on_prompt_selected(self, index: int) -> None:
        """Copy the selected predefined prompt into the editor."""
        if index < 0:
            return
        full_text = self._prompt_combo.itemData(index)
        if full_text:
            self._editor.blockSignals(True)
            self._editor.setPlainText(full_text)
            self._editor.blockSignals(False)
            self._on_text_changed()

    def _on_text_changed(self) -> None:
        """Enforce max length and update character counter."""
        text = self._editor.toPlainText()
        length = len(text)

        # Enforce max length
        if length > _MAX_PROMPT_CHARS:
            cursor = self._editor.textCursor()
            self._editor.blockSignals(True)
            self._editor.setPlainText(text[:_MAX_PROMPT_CHARS])
            cursor.movePosition(cursor.MoveOperation.End)
            self._editor.setTextCursor(cursor)
            self._editor.blockSignals(False)
            length = _MAX_PROMPT_CHARS

        # Update counter
        self._char_counter.setText(f"{length} / {_MAX_PROMPT_CHARS}")
        if length > _MAX_PROMPT_CHARS * 0.9:
            self._char_counter.setObjectName("CharCounterWarn")
        else:
            self._char_counter.setObjectName("CharCounter")
        self._char_counter.style().unpolish(self._char_counter)
        self._char_counter.style().polish(self._char_counter)

        self._update_run_button_state()

    def _update_run_button_state(self) -> None:
        """Enable/disable the Run button based on current state."""
        has_prompt = bool(self._editor.toPlainText().strip())
        has_model = self._model is not None
        is_idle = self._worker is None or not self._worker.isRunning()
        self._run_btn.setEnabled(has_prompt and has_model and is_idle)

    # ── Run prompt ───────────────────────────────────────────────────

    def _on_run_clicked(self) -> None:
        """Validate and launch inference in a background thread."""
        prompt = self._editor.toPlainText().strip()

        if not prompt:
            QMessageBox.warning(
                self,
                "Empty Prompt",
                "Please enter a prompt before running.",
            )
            return

        if self._model is None:
            QMessageBox.warning(
                self,
                "No Model Loaded",
                "Please upload and load a model before running prompts.",
            )
            return

        # Read generation params from sliders
        from services.prompt_execution_service import GenerationParams

        params = GenerationParams(
            temperature=self._temp_slider.value() / 10.0,
            top_p=self._top_p_slider.value() / 20.0,
            top_k=self._top_k_slider.value(),
            max_new_tokens=self._max_tok_slider.value() * 16,
        )

        category = self._category_combo.currentText()

        # Disable UI during inference
        self._run_btn.setEnabled(False)
        self._running_label.setText("⏳  Generating…")
        self._running_label.show()
        self._response_display.setPlainText("")
        self._clear_stats()

        # Launch worker
        self._worker = _InferenceWorker(
            prompt=prompt,
            model=self._model,
            tokenizer=self._tokenizer,
            category=category,
            model_id=self._model_id,
            params=params,
            parent=self,
        )
        self._worker.finished.connect(self._on_inference_finished)
        self._worker.error.connect(self._on_inference_error)
        self._worker.start()

    def _on_inference_finished(self, result) -> None:
        """Handle a completed inference."""
        self._running_label.hide()
        self._update_run_button_state()

        if result.status == "error":
            self._response_display.setPlainText(
                f"[Error] {result.error_message}"
            )
            self._update_stats(result)
            QMessageBox.warning(
                self,
                "Generation Error",
                result.error_message,
            )
            return

        # Show response
        self._response_display.setPlainText(result.response)

        # Show statistics
        self._update_stats(result)

        # Persist to database
        self._save_to_history(result)

        # Refresh history table
        self._refresh_history()

    def _on_inference_error(self, message: str) -> None:
        """Handle a fatal worker error."""
        self._running_label.hide()
        self._update_run_button_state()

        QMessageBox.critical(
            self,
            "Inference Failed",
            f"An unexpected error occurred:\n\n{message}",
        )

    # ── Stats display ────────────────────────────────────────────────

    def _update_stats(self, result) -> None:
        """Populate the statistics grid from a PromptExecutionResult."""
        self._stat_labels["Input Tokens"].setText(str(result.input_tokens))
        self._stat_labels["Output Tokens"].setText(str(result.output_tokens))
        self._stat_labels["Characters"].setText(str(result.characters_generated))
        self._stat_labels["Inference Time"].setText(f"{result.inference_time:.2f}s")

        avg_label = self._stat_labels["Avg Tokens/s"]
        avg_label.setText(f"{result.avg_tokens_per_second:.1f}")
        avg_label.setObjectName("StatValueAccent")
        avg_label.style().unpolish(avg_label)
        avg_label.style().polish(avg_label)

        status_label = self._stat_labels["Status"]
        if result.status == "success":
            status_label.setText("✔ Success")
            status_label.setObjectName("StatusSuccess")
        else:
            status_label.setText("✖ Error")
            status_label.setObjectName("StatusError")
        status_label.style().unpolish(status_label)
        status_label.style().polish(status_label)

    def _clear_stats(self) -> None:
        for lbl in self._stat_labels.values():
            lbl.setText("—")
            lbl.setObjectName("StatValue")
            lbl.style().unpolish(lbl)
            lbl.style().polish(lbl)

    # ── Database persistence ─────────────────────────────────────────

    def _save_to_history(self, result) -> None:
        """Persist a successful execution to the prompt_history table."""
        try:
            from database.database import DatabaseManager
            from database.models import PromptHistoryRecord

            record = PromptHistoryRecord(
                model_id=self._model_id,
                category=result.category,
                prompt=result.prompt,
                response=result.response,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                inference_time=result.inference_time,
                created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
            db = DatabaseManager()
            db.insert_prompt_history(record)
            log.info("Prompt execution saved to database.")
        except Exception as exc:
            log.error("Failed to save prompt history: %s", exc)

    def _refresh_history(self) -> None:
        """Reload the history table from the database."""
        try:
            from database.database import DatabaseManager

            db = DatabaseManager()
            records = db.get_prompt_history(limit=50)
        except Exception:
            records = []

        self._history_table.setRowCount(len(records))

        for row_idx, rec in enumerate(records):
            # Time
            time_item = QTableWidgetItem(rec.created_at)
            time_item.setFlags(
                Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
            )
            self._history_table.setItem(row_idx, 0, time_item)

            # Category
            cat_item = QTableWidgetItem(rec.category)
            cat_item.setFlags(
                Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
            )
            self._history_table.setItem(row_idx, 1, cat_item)

            # Prompt preview
            preview = rec.prompt[:60] + "…" if len(rec.prompt) > 60 else rec.prompt
            prompt_item = QTableWidgetItem(preview)
            prompt_item.setFlags(
                Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
            )
            prompt_item.setToolTip(rec.prompt[:300])
            self._history_table.setItem(row_idx, 2, prompt_item)

            # Response preview
            resp_preview = rec.response[:60] + "…" if len(rec.response) > 60 else rec.response
            resp_item = QTableWidgetItem(resp_preview)
            resp_item.setFlags(
                Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
            )
            resp_item.setToolTip(rec.response[:300])
            self._history_table.setItem(row_idx, 3, resp_item)

            # Inference time
            time_val = QTableWidgetItem(f"{rec.inference_time:.2f}")
            time_val.setFlags(
                Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
            )
            self._history_table.setItem(row_idx, 4, time_val)

    # ── Slider builder ───────────────────────────────────────────────

    @staticmethod
    def _make_slider(
        label: str,
        minimum: int,
        maximum: int,
        default: int,
        grid: QGridLayout,
        row: int,
        *,
        fmt: callable,
    ) -> tuple[QSlider, QLabel]:
        """Create a labelled horizontal slider and add it to *grid*."""
        name_lbl = QLabel(label)
        name_lbl.setObjectName("SliderLabel")
        grid.addWidget(name_lbl, row, 0)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(minimum, maximum)
        slider.setValue(default)
        slider.setFixedHeight(22)
        grid.addWidget(slider, row, 1)

        val_lbl = QLabel(fmt(default))
        val_lbl.setObjectName("SliderValue")
        val_lbl.setFixedWidth(50)
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(val_lbl, row, 2)

        return slider, val_lbl
