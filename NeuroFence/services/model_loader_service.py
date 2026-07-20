"""Model loader service for NeuroFence.

Orchestrates the end-to-end "Scan Model" pipeline:

    Resolve model path → Inspect model → Store results in SQLite → Return result

This thin wrapper keeps orchestration concerns separate from the raw
Transformers loading logic in :class:`ModelInspectionService`.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from database.database import DatabaseManager
from database.models import ModelInspectionRecord, ModelInspectionResult, ModelRecord
from services.model_inspection_service import ModelInspectionService, ModelLoadError

log = logging.getLogger(__name__)


class ModelLoaderService:
    """Stateless service that loads a model and persists the results.

    Usage::

        service = ModelLoaderService()
        result = service.load_and_inspect(model_record)
    """

    def __init__(self) -> None:
        self._db = DatabaseManager()
        self._inspector = ModelInspectionService()

    # ── Public API ───────────────────────────────────────────────────

    def load_and_inspect(
        self,
        record: ModelRecord,
        *,
        progress_callback: callable | None = None,
    ) -> ModelInspectionResult:
        """Load the model described by *record* and store inspection data.

        Args:
            record: The :class:`ModelRecord` from the upload step.
            progress_callback: Optional callable accepting an ``int``
                               percentage (0–100) for UI progress updates.

        Returns:
            A :class:`ModelInspectionResult` with all extracted architecture info.

        Raises:
            ModelLoadError: If loading or inspection fails.
        """
        model_path = Path(record.filepath)
        log.info("Starting model load for: %s", model_path)

        # ── Run inspection ────────────────────────────────────────────
        result = self._inspector.inspect(
            model_path,
            progress_callback=progress_callback,
        )

        # ── Persist to SQLite ─────────────────────────────────────────
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        inspection_record = ModelInspectionRecord(
            model_id=record.id or 0,
            architecture=result.architecture,
            layers=result.layers,
            hidden_size=result.hidden_size,
            vocab_size=result.vocab_size,
            context_length=result.context_length,
            attention_heads=result.attention_heads,
            parameter_count=result.parameter_count,
            dtype=result.dtype,
            device=result.device,
            loaded_at=now,
        )

        try:
            self._db.insert_inspection(inspection_record)
            log.info("Inspection results stored in database.")
        except Exception as exc:
            log.error("Failed to store inspection results: %s", exc)
            # Non-fatal — return the result even if DB write fails

        return result
