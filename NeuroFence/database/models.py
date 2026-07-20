"""Data-transfer objects for database records.

Each dataclass mirrors a single database table and serves as the
canonical shape for data flowing between the service layer and the UI.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


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
