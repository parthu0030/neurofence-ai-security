"""Model upload orchestration service for NeuroFence.

Coordinates the complete upload pipeline:

    File Dialog → Validate Extension → Copy File → Hash
    → Extract Metadata → Save to DB → Return ModelRecord

All UI interaction is limited to the native file dialog and error
message boxes; the caller is responsible for updating its own widgets.
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget

from config.settings import Paths
from database.database import DatabaseManager
from database.models import ModelRecord
from utils.file_metadata import extract_metadata
from utils.hash_generator import HashGenerator

# ── Allowed file extensions ──────────────────────────────────────────────
ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".safetensors", ".bin", ".pt"})

# File-dialog filter string for QFileDialog.
_DIALOG_FILTER: str = (
    "AI Model Files (*.safetensors *.bin *.pt);;"
    "All Files (*)"
)


class InvalidFileTypeError(Exception):
    """Raised when a file with a disallowed extension is selected."""


class ModelUploadService:
    """Stateless service that processes a single model upload.

    Usage::

        service = ModelUploadService()
        record = service.process_upload(parent_widget)
        if record:
            # update UI …
    """

    def __init__(self) -> None:
        self._db = DatabaseManager()

    # ── Public API ───────────────────────────────────────────────────

    def process_upload(self, parent: QWidget | None = None) -> ModelRecord | None:
        """Run the full upload pipeline.

        Returns a :class:`ModelRecord` on success, or ``None`` if the
        user cancelled the file dialog.
        """
        filepath = self._open_file_dialog(parent)
        if filepath is None:
            return None

        try:
            self._validate_extension(filepath)
        except InvalidFileTypeError:
            self._show_error_dialog(filepath, parent)
            return None

        dest = self._copy_to_uploads(filepath)
        sha256 = HashGenerator.sha256(dest)
        meta = extract_metadata(dest)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = ModelRecord(
            filename=meta.filename,
            filepath=meta.filepath,
            extension=meta.extension,
            size=meta.size_bytes,
            sha256=sha256,
            created_at=meta.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            modified_at=meta.modified_at.strftime("%Y-%m-%d %H:%M:%S"),
            uploaded_at=now,
        )

        self._db.insert_model(record)
        return record

    # ── Private helpers ──────────────────────────────────────────────

    @staticmethod
    def _open_file_dialog(parent: QWidget | None) -> Path | None:
        """Show a native file picker filtered to model files."""
        path_str, _ = QFileDialog.getOpenFileName(
            parent,
            "Select AI Model File",
            "",
            _DIALOG_FILTER,
        )
        if not path_str:
            return None
        return Path(path_str)

    @staticmethod
    def _validate_extension(filepath: Path) -> None:
        """Raise :class:`InvalidFileTypeError` if the extension is invalid."""
        ext = filepath.suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise InvalidFileTypeError(
                f"File type '{ext}' is not supported. "
                f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

    @staticmethod
    def _copy_to_uploads(filepath: Path) -> Path:
        """Copy the file into the ``uploads/`` directory.

        If a file with the same name already exists, it is replaced.
        """
        uploads_dir = Paths.UPLOADS
        uploads_dir.mkdir(parents=True, exist_ok=True)
        dest = uploads_dir / filepath.name
        shutil.copy2(str(filepath), str(dest))
        return dest

    @staticmethod
    def _show_error_dialog(filepath: Path, parent: QWidget | None) -> None:
        """Display a professional error dialog for invalid file types."""
        ext = filepath.suffix.lower()
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Invalid File Type")
        msg.setText(f"Cannot upload \"{filepath.name}\"")
        msg.setInformativeText(
            f"The file extension \"{ext}\" is not supported.\n\n"
            f"NeuroFence only accepts AI model files with the\n"
            f"following extensions:\n\n"
            f"    •  .safetensors\n"
            f"    •  .bin\n"
            f"    •  .pt\n\n"
            f"Please select a valid model file."
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
