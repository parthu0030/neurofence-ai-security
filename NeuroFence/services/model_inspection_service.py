"""Model inspection service for NeuroFence.

Loads a Hugging Face model locally, reads its configuration and
tokenizer, and returns a structured :class:`ModelInspectionResult`
with all extracted architecture information.

This service contains **no UI code** — it is pure business logic.
"""

from __future__ import annotations

import logging
from pathlib import Path

import torch
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer

from database.models import ModelInspectionResult
from utils.device_detector import DeviceInfo, detect_device
from utils.file_metadata import _derive_model_name

log = logging.getLogger(__name__)


class ModelLoadError(Exception):
    """Raised when model loading or inspection fails."""


class ModelInspectionService:
    """Loads a model from disk and extracts its architecture information.

    Usage::

        service = ModelInspectionService()
        result = service.inspect(Path("uploads/tinyllama-1.1b/"))
    """

    def __init__(self) -> None:
        self._device_info: DeviceInfo = detect_device()

    # ── Public API ───────────────────────────────────────────────────

    def inspect(
        self,
        model_path: Path,
        *,
        progress_callback: callable | None = None,
    ) -> ModelInspectionResult:
        """Run the full inspection pipeline on *model_path*.

        Args:
            model_path: Path to a directory containing ``config.json``,
                        tokenizer files, and model weight files.
            progress_callback: Optional callable accepting an ``int``
                               percentage (0–100) for progress updates.

        Returns:
            A fully populated :class:`ModelInspectionResult`.

        Raises:
            ModelLoadError: If any step of loading fails.
        """
        model_dir = self._resolve_model_directory(model_path)
        model_dir_str = str(model_dir)

        try:
            # ── Step 1: Load configuration (10 %) ─────────────────────
            self._emit(progress_callback, 10)
            log.info("Loading configuration from %s", model_dir)
            config = AutoConfig.from_pretrained(model_dir_str)

            # ── Step 2: Load tokenizer (40 %) ─────────────────────────
            self._emit(progress_callback, 40)
            log.info("Loading tokenizer from %s", model_dir)
            tokenizer_loaded = True
            try:
                tokenizer = AutoTokenizer.from_pretrained(model_dir_str)
            except Exception as exc:
                log.warning("Tokenizer load failed (%s), continuing without it.", exc)
                tokenizer = None
                tokenizer_loaded = False

            # ── Step 3: Load model weights (70 %) ─────────────────────
            self._emit(progress_callback, 70)
            log.info(
                "Loading model weights onto %s from %s",
                self._device_info.device_type,
                model_dir,
            )
            model = AutoModelForCausalLM.from_pretrained(
                model_dir_str,
                torch_dtype=torch.float16 if self._device_info.is_gpu else torch.float32,
                device_map=self._device_info.device_name,
                low_cpu_mem_usage=True,
            )

            # ── Step 4: Extract information (100 %) ───────────────────
            self._emit(progress_callback, 100)
            log.info("Model loaded successfully — extracting architecture info.")

            result = self._extract_info(
                config=config,
                model=model,
                model_dir=model_dir,
                tokenizer_loaded=tokenizer_loaded,
            )

            # Free GPU memory after inspection
            del model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            return result

        except ModelLoadError:
            raise
        except torch.cuda.OutOfMemoryError as exc:
            raise ModelLoadError(
                "Insufficient GPU memory to load this model. "
                "Try a smaller model or use CPU mode."
            ) from exc
        except (OSError, ValueError) as exc:
            raise ModelLoadError(
                f"Failed to load model from '{model_dir}': {exc}"
            ) from exc
        except RuntimeError as exc:
            raise ModelLoadError(
                f"Runtime error during model loading: {exc}"
            ) from exc
        except Exception as exc:
            raise ModelLoadError(
                f"Unexpected error during model inspection: {exc}"
            ) from exc

    # ── Private helpers ──────────────────────────────────────────────

    @staticmethod
    def _resolve_model_directory(model_path: Path) -> Path:
        """Locate the directory containing ``config.json``.

        If *model_path* is a file, check its parent directory.
        If *model_path* is already a directory, use it directly.
        """
        model_path = Path(model_path).resolve()

        if model_path.is_file():
            candidate = model_path.parent
        else:
            candidate = model_path

        if (candidate / "config.json").exists():
            return candidate

        # Check one level up (in case uploads/ structure nests files)
        parent = candidate.parent
        if (parent / "config.json").exists():
            return parent

        raise ModelLoadError(
            f"Cannot find 'config.json' in '{candidate}' or its parent. "
            f"Please upload a complete Hugging Face model directory."
        )

    def _extract_info(
        self,
        config,
        model,
        model_dir: Path,
        tokenizer_loaded: bool,
    ) -> ModelInspectionResult:
        """Extract architecture details from the loaded config and model."""
        # Architecture name — use the model class name from config
        architecture = getattr(config, "architectures", ["Unknown"])
        if isinstance(architecture, list):
            architecture = architecture[0] if architecture else "Unknown"

        # Layer count — try several config attribute names
        layers = (
            getattr(config, "num_hidden_layers", None)
            or getattr(config, "n_layer", None)
            or getattr(config, "num_layers", None)
            or 0
        )

        hidden_size = getattr(config, "hidden_size", 0)
        vocab_size = getattr(config, "vocab_size", 0)

        # Context length — several possible attribute names
        context_length = (
            getattr(config, "max_position_embeddings", None)
            or getattr(config, "n_positions", None)
            or getattr(config, "max_sequence_length", None)
            or 0
        )

        attention_heads = (
            getattr(config, "num_attention_heads", None)
            or getattr(config, "n_head", None)
            or 0
        )

        # Parameter count
        try:
            parameter_count = model.num_parameters()
        except Exception:
            parameter_count = sum(p.numel() for p in model.parameters())

        # Data type
        dtype = str(model.dtype)

        # Model name
        model_name = _derive_model_name(model_dir.name)

        return ModelInspectionResult(
            model_name=model_name,
            architecture=architecture,
            layers=layers,
            hidden_size=hidden_size,
            vocab_size=vocab_size,
            context_length=context_length,
            attention_heads=attention_heads,
            parameter_count=parameter_count,
            dtype=dtype,
            device=self._device_info.device_type,
            model_loaded=True,
            tokenizer_loaded=tokenizer_loaded,
        )

    @staticmethod
    def _emit(callback: callable | None, value: int) -> None:
        """Safely call *callback* with *value* if it is not None."""
        if callback is not None:
            callback(value)
