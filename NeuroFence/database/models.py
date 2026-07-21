"""Data-transfer objects for database records.

Each dataclass mirrors a single database table and serves as the
canonical shape for data flowing between the service layer and the UI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ModelRecord:
    """Represents a row in the ``uploaded_models`` table.

    Attributes:
        id:          Auto-incremented primary key (``None`` before insertion).
        filename:    Original file name, e.g. ``"tinyllama-1.1b.safetensors"``.
        filepath:    Absolute path to the file inside ``uploads/``.
        extension:   Lowercase extension, e.g. ``".safetensors"``.
        size:        File size in bytes.
        sha256:      Hex-encoded SHA-256 fingerprint.
        created_at:  File creation timestamp.
        modified_at: File last-modified timestamp.
        uploaded_at: Timestamp of the upload event.
    """

    filename: str
    filepath: str
    extension: str
    size: int
    sha256: str
    created_at: str
    modified_at: str
    uploaded_at: str
    id: int | None = None


@dataclass
class ModelInspectionRecord:
    """Represents a row in the ``model_inspection`` table.

    This is the persistence-layer DTO written to and read from SQLite.

    Attributes:
        model_id:        Foreign key referencing ``uploaded_models.id``.
        architecture:    Model class name, e.g. ``"LlamaForCausalLM"``.
        layers:          Number of transformer layers.
        hidden_size:     Dimensionality of the hidden states.
        vocab_size:      Size of the tokenizer vocabulary.
        context_length:  Maximum sequence length the model supports.
        attention_heads: Number of attention heads per layer.
        parameter_count: Total trainable parameters (may be ``None``).
        dtype:           Torch data type string, e.g. ``"torch.float16"``.
        device:          Device string — ``"cpu"``, ``"mps"``, or ``"cuda"``.
        loaded_at:       ISO timestamp of the loading event.
        id:              Auto-incremented primary key (``None`` before insertion).
    """

    model_id: int
    architecture: str
    layers: int
    hidden_size: int
    vocab_size: int
    context_length: int
    attention_heads: int
    dtype: str
    device: str
    loaded_at: str
    parameter_count: int | None = None
    id: int | None = None


@dataclass
class ModelInspectionResult:
    """Rich result object returned by the inspection service.

    Carries everything the UI needs to display after a successful
    model load — separate from the DB record so the UI layer never
    touches ``ModelInspectionRecord`` directly.

    ``model_ref`` and ``tokenizer_ref`` hold the live Transformers
    objects so the prompt-execution engine can reuse them without
    reloading from disk.  They are **not** persisted to the database.
    """

    model_name: str
    architecture: str
    layers: int
    hidden_size: int
    vocab_size: int
    context_length: int
    attention_heads: int
    parameter_count: int | None
    dtype: str
    device: str
    model_loaded: bool
    tokenizer_loaded: bool
    model_ref: Any = field(default=None, repr=False)
    tokenizer_ref: Any = field(default=None, repr=False)


# ═══════════════════════════════════════════════════════════════════════════
#  Prompt Execution DTOs
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class PromptHistoryRecord:
    """Represents a row in the ``prompt_history`` table.

    Attributes:
        model_id:       Foreign key referencing ``uploaded_models.id``.
        category:       Prompt category (Normal, Coding, Safety, …).
        prompt:         The full prompt text sent to the model.
        response:       The generated response text.
        input_tokens:   Number of tokens in the prompt.
        output_tokens:  Number of newly generated tokens.
        inference_time: Wall-clock generation time in seconds.
        created_at:     ISO timestamp of the execution.
        id:             Auto-incremented primary key (``None`` before insertion).
    """

    model_id: int
    category: str
    prompt: str
    response: str
    input_tokens: int
    output_tokens: int
    inference_time: float
    created_at: str
    id: int | None = None


@dataclass
class PromptExecutionResult:
    """UI-facing result returned by :class:`PromptExecutionService`.

    Includes all raw data plus computed statistics so the UI never
    has to compute anything itself.

    Attributes:
        prompt:                 The original prompt text.
        response:               The generated response text.
        category:               Prompt category label.
        input_tokens:           Token count of the input.
        output_tokens:          Token count of the generated output.
        characters_generated:   ``len(response)``.
        inference_time:         Wall-clock seconds for generation.
        avg_tokens_per_second:  ``output_tokens / inference_time``.
        status:                 ``"success"`` or ``"error"``.
        error_message:          Human-readable error (empty on success).
    """

    prompt: str
    response: str
    category: str
    input_tokens: int
    output_tokens: int
    characters_generated: int
    inference_time: float
    avg_tokens_per_second: float
    status: str = "success"
    error_message: str = ""
