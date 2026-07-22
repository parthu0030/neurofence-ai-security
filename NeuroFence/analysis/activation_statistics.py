"""Activation statistics computation for NeuroFence.

Pure-computation module that calculates summary statistics from
captured activation tensors.  Contains no UI, no database, and no
I/O logic — only ``torch`` math.

Usage::

    from analysis.activation_statistics import compute_layer_stats, compute_summary

    stat = compute_layer_stats(layer_idx=0, tensor=hidden_state)
    summary = compute_summary([stat, ...])
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import torch

log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
#  Data Transfer Objects
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class LayerActivation:
    """Summary statistics for a single transformer layer's hidden state.

    Attributes:
        layer_number:  Zero-based index of the transformer layer.
        tensor_shape:  String representation of the tensor shape,
                       e.g. ``"(1, 128, 2048)"``.
        mean:          Mean value of all elements.
        std:           Standard deviation.
        max:           Maximum activation value.
        min:           Minimum activation value.
        norm:          L2 (Frobenius) norm of the flattened tensor.
    """

    layer_number: int
    tensor_shape: str
    mean: float
    std: float
    max: float
    min: float
    norm: float


@dataclass
class ActivationSummary:
    """Aggregate result for all layers captured during one prompt execution.

    Attributes:
        layers:             Per-layer statistics.
        layers_captured:    Total number of layers whose activations were captured.
        average_activation: Grand mean across all layers.
        peak_activation:    Maximum absolute activation across all layers.
        capture_successful: Whether the capture completed without error.
    """

    layers: list[LayerActivation] = field(default_factory=list)
    layers_captured: int = 0
    average_activation: float = 0.0
    peak_activation: float = 0.0
    capture_successful: bool = False


# ═══════════════════════════════════════════════════════════════════════════
#  Computation helpers
# ═══════════════════════════════════════════════════════════════════════════


def compute_layer_stats(layer_idx: int, tensor: torch.Tensor) -> LayerActivation:
    """Compute summary statistics for a single layer's activation tensor.

    The tensor is processed under ``torch.no_grad()`` and detached to
    avoid interfering with the computation graph or leaking GPU memory.

    Args:
        layer_idx: Zero-based index of the transformer layer.
        tensor:    The hidden-state tensor captured by the forward hook.

    Returns:
        A :class:`LayerActivation` with all six summary statistics.
    """
    with torch.no_grad():
        t = tensor.detach().float()  # ensure float for stable statistics

        shape_str = str(tuple(t.shape))
        mean_val = t.mean().item()
        std_val = t.std().item()
        max_val = t.max().item()
        min_val = t.min().item()
        norm_val = t.norm(p=2).item()

    return LayerActivation(
        layer_number=layer_idx,
        tensor_shape=shape_str,
        mean=round(mean_val, 6),
        std=round(std_val, 6),
        max=round(max_val, 6),
        min=round(min_val, 6),
        norm=round(norm_val, 4),
    )


def compute_summary(activations: list[LayerActivation]) -> ActivationSummary:
    """Build an :class:`ActivationSummary` from a list of layer statistics.

    Args:
        activations: List of :class:`LayerActivation` objects, one per
                     captured layer.

    Returns:
        An :class:`ActivationSummary` with aggregate metrics.
    """
    if not activations:
        return ActivationSummary(capture_successful=False)

    layers_captured = len(activations)
    avg_activation = sum(a.mean for a in activations) / layers_captured
    peak_activation = max(
        max(abs(a.max), abs(a.min)) for a in activations
    )

    return ActivationSummary(
        layers=activations,
        layers_captured=layers_captured,
        average_activation=round(avg_activation, 6),
        peak_activation=round(peak_activation, 6),
        capture_successful=True,
    )
