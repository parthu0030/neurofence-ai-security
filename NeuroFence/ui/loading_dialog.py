"""Professional model-loading dialog for NeuroFence.

Displays an animated progress bar while a QThread worker loads the
model in the background.  Emits ``model_loaded(ModelInspectionResult)``
on success or shows a friendly error dialog on failure.
"""

from __future__ import annotations

import logging

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QMessageBox,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from config.settings import ThemeColors
from database.models import ModelInspectionResult, ModelRecord

log = logging.getLogger(__name__)
_T = ThemeColors()


# ═══════════════════════════════════════════════════════════════════════════
#  Background worker thread
# ═══════════════════════════════════════════════════════════════════════════


class _ModelLoaderWorker(QThread):
    """Runs the model loading pipeline off the main thread."""

    progress = pyqtSignal(int)
    finished = pyqtSignal(object)   # ModelInspectionResult
    error = pyqtSignal(str)

    def __init__(self, record: ModelRecord, parent: QThread | None = None) -> None:
        super().__init__(parent)
        self._record = record

    def run(self) -> None:
        try:
            from services.model_loader_service import ModelLoaderService

            service = ModelLoaderService()
            result = service.load_and_inspect(
                self._record,
                progress_callback=self._on_progress,
            )
            self.finished.emit(result)
        except Exception as exc:
            log.exception("Model loading failed.")
            self.error.emit(str(exc))

    def _on_progress(self, value: int) -> None:
        self.progress.emit(value)


# ═══════════════════════════════════════════════════════════════════════════
#  Loading dialog
# ═══════════════════════════════════════════════════════════════════════════

_DIALOG_STYLESHEET = f"""
QDialog#LoadingDialog {{
    background-color: {_T.bg_panel};
    border: 1px solid {_T.border};
    border-radius: 16px;
}}

QLabel#LoadingTitle {{
    color: {_T.text_primary};
    font-size: 18px;
    font-weight: 700;
    padding-top: 8px;
}}

QLabel#LoadingSubtitle {{
    color: {_T.text_secondary};
    font-size: 13px;
    font-weight: 400;
}}

QLabel#LoadingPercent {{
    color: {_T.accent_light};
    font-size: 28px;
    font-weight: 700;
    font-family: "Menlo", "Courier New", monospace;
}}

QLabel#LoadingStatus {{
    color: {_T.text_muted};
    font-size: 12px;
}}

QLabel#LoadingSuccess {{
    color: {_T.success};
    font-size: 14px;
    font-weight: 600;
}}

QProgressBar {{
    background-color: {_T.bg_input};
    border: 1px solid {_T.border};
    border-radius: 8px;
    height: 18px;
    text-align: center;
    color: transparent;
}}

QProgressBar::chunk {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {_T.accent}, stop:1 {_T.accent_light}
    );
    border-radius: 7px;
}}
"""

_STEP_LABELS: dict[int, str] = {
    0: "Preparing model loader…",
    10: "Reading model configuration…",
    40: "Loading tokenizer…",
    70: "Loading model weights into memory…",
    100: "Extracting architecture information…",
}


class LoadingDialog(QDialog):
    """Modal dialog with animated progress bar for model loading.

    Signals:
        model_loaded(ModelInspectionResult): Emitted on success.
    """

    model_loaded = pyqtSignal(object)

    DIALOG_WIDTH = 440
    DIALOG_HEIGHT = 300

    def __init__(
        self,
        record: ModelRecord,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("LoadingDialog")
        self.setWindowTitle("NeuroFence — Loading Model")
        self.setFixedSize(self.DIALOG_WIDTH, self.DIALOG_HEIGHT)
        self.setModal(True)
        self.setStyleSheet(_DIALOG_STYLESHEET)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
        )

        self._record = record
        self._worker: _ModelLoaderWorker | None = None

        self._build_ui()
        self._start_loading()

    # ── UI construction ───────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon
        icon = QLabel("🧠")
        icon.setStyleSheet("font-size: 36px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        # Title
        title = QLabel("Loading Model…")
        title.setObjectName("LoadingTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Please wait while NeuroFence initializes the LLM.")
        subtitle.setObjectName("LoadingSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        # Percentage label
        self._percent_label = QLabel("0%")
        self._percent_label.setObjectName("LoadingPercent")
        self._percent_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._percent_label)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setFixedHeight(18)
        layout.addWidget(self._progress_bar)

        # Step description
        self._step_label = QLabel("Preparing model loader…")
        self._step_label.setObjectName("LoadingStatus")
        self._step_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._step_label)

        # Success label (hidden initially)
        self._success_label = QLabel("")
        self._success_label.setObjectName("LoadingSuccess")
        self._success_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._success_label.hide()
        layout.addWidget(self._success_label)

    # ── Worker management ─────────────────────────────────────────────

    def _start_loading(self) -> None:
        self._worker = _ModelLoaderWorker(self._record, parent=self)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, value: int) -> None:
        self._progress_bar.setValue(value)
        self._percent_label.setText(f"{value}%")
        step_text = _STEP_LABELS.get(value, "")
        if step_text:
            self._step_label.setText(step_text)

    def _on_finished(self, result: ModelInspectionResult) -> None:
        self._progress_bar.setValue(100)
        self._percent_label.setText("100%")
        self._step_label.hide()

        self._success_label.setText("✔ Model Loaded Successfully")
        self._success_label.show()

        self.model_loaded.emit(result)

        # Auto-close after a brief moment so the user sees the success
        QTimer.singleShot(1_200, self.accept)

    def _on_error(self, message: str) -> None:
        self.reject()
        self._show_error_dialog(message)

    # ── Error dialog ──────────────────────────────────────────────────

    def _show_error_dialog(self, detail: str) -> None:
        msg = QMessageBox(self.parent())
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Model Loading Failed")
        msg.setText("Unable to load model.")
        msg.setInformativeText(
            "Possible reasons:\n\n"
            "    •  Corrupted model files\n"
            "    •  Unsupported format\n"
            "    •  Missing config.json or tokenizer files\n"
            "    •  Insufficient memory\n\n"
            f"Details:\n{detail}"
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    # ── Cleanup ───────────────────────────────────────────────────────

    def closeEvent(self, event) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait(3_000)
        super().closeEvent(event)
