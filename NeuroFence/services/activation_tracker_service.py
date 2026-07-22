"""Activation tracker service for NeuroFence.

Manages the lifecycle of PyTorch forward hooks on transformer layers:
register → capture → compute statistics → clear buffers.

This module contains **no UI code** — it is pure business logic.

Usage::

    tracker = ActivationTrackerService()
    tracker.register_hooks(model)
    # … run inference …
    summary = tracker.process_activations()
    tracker.clear()
"""

from __future__ import annotations

import logging
from typing import Any

import torch
from torch import nn
from torch.utils.hooks import RemovableHandle

from analysis.activation_statistics import (
    ActivationSummary,
    LayerActivation,
    compute_layer_stats,
    compute_summary,
)

log = logging.getLogger(__name__)

# ── Known transformer decoder-layer class names ─────────────────────────
# Used for reliable detection across model families.
_KNOWN_LAYER_NAMES: frozenset[str] = frozenset(
    {
        "LlamaDecoderLayer",
        "GPT2Block",
        "GPTNeoBlock",
        "GPTNeoXLayer",
        "PhiDecoderLayer",
        "Phi3DecoderLayer",
        "GemmaDecoderLayer",
        "Gemma2DecoderLayer",
        "MistralDecoderLayer",
        "QwenDecoderLayer",
        "Qwen2DecoderLayer",
        "FalconDecoderLayer",
        "BloomBlock",
        "OPTDecoderLayer",
        "StableLmDecoderLayer",
    }
)

# Fallback patterns — if the class name contains any of these substrings
# it is almost certainly a transformer block.
_FALLBACK_PATTERNS: tuple[str, ...] = ("DecoderLayer", "Block", "TransformerLayer")


class ActivationTrackerError(Exception):
    """Raised when activation tracking fails in a recoverable way."""


class ActivationTrackerService:
    """Registers forward hooks on transformer layers and captures activations.

    Designed to be instantiated once per model load and reused across
    multiple prompt executions.
    """

    def __init__(self) -> None:
        self._hooks: list[RemovableHandle] = []
        self._captured: list[tuple[int, torch.Tensor]] = []
        self._layer_count: int = 0

    # ── Properties ───────────────────────────────────────────────────

    @property
    def has_hooks(self) -> bool:
        """Return ``True`` if hooks are currently registered."""
        return len(self._hooks) > 0

    @property
    def layer_count(self) -> int:
        """Return the number of transformer layers with hooks."""
        return self._layer_count

    # ── Public API ───────────────────────────────────────────────────

    def register_hooks(self, model: nn.Module) -> bool:
        """Register forward hooks on every detected transformer layer.

        If hooks are already registered they are removed first to avoid
        duplicate registrations.

        Args:
            model: A loaded ``AutoModelForCausalLM`` instance.

        Returns:
            ``True`` if at least one hook was registered, ``False``
            otherwise (i.e. no transformer layers were found).
        """
        # Safety — remove any stale hooks
        if self._hooks:
            self.remove_hooks()

        layers = self._find_transformer_layers(model)

        if not layers:
            log.warning(
                "No transformer layers detected in model %s — "
                "activation tracking will be unavailable.",
                type(model).__name__,
            )
            return False

        for idx, (name, module) in enumerate(layers):
            handle = module.register_forward_hook(self._make_hook_fn(idx))
            self._hooks.append(handle)
            log.debug("Hook registered on layer %d (%s)", idx, name)

        self._layer_count = len(layers)
        log.info(
            "Registered %d forward hooks on %s.",
            self._layer_count,
            type(model).__name__,
        )
        return True

    def remove_hooks(self) -> None:
        """Remove all registered forward hooks safely."""
        for handle in self._hooks:
            try:
                handle.remove()
            except Exception as exc:  # noqa: BLE001
                log.warning("Failed to remove hook: %s", exc)
        removed = len(self._hooks)
        self._hooks.clear()
        self._layer_count = 0
        log.info("Removed %d forward hooks.", removed)

    def process_activations(self) -> ActivationSummary | None:
        """Compute summary statistics from captured activations.

        After computing the summary the internal capture buffer is
        cleared to free memory.

        Returns:
            An :class:`ActivationSummary` on success, or ``None``
            if nothing was captured.
        """
        if not self._captured:
            log.warning("No activations captured — nothing to process.")
            return None

        try:
            layer_stats: list[LayerActivation] = []
            for layer_idx, tensor in self._captured:
                stat = compute_layer_stats(layer_idx, tensor)
                layer_stats.append(stat)

            summary = compute_summary(layer_stats)
            log.info(
                "Processed activations: %d layers, avg=%.6f, peak=%.6f",
                summary.layers_captured,
                summary.average_activation,
                summary.peak_activation,
            )
            return summary

        except Exception as exc:
            log.exception("Failed to process activations: %s", exc)
            return None

        finally:
            # Always clear the buffer to prevent memory leaks
            self._clear_captured()

    def clear(self) -> None:
        """Clear all cached activations and summaries."""
        self._clear_captured()

    # ── Private helpers ──────────────────────────────────────────────

    def _make_hook_fn(self, layer_idx: int):
        """Return a closure that captures the hidden state for *layer_idx*."""

        def _hook(
            module: nn.Module,
            input: Any,  # noqa: A002
            output: Any,
        ) -> None:
            try:
                tensor = self._extract_hidden_state(output)
                if tensor is not None:
                    # Detach immediately to avoid graph retention
                    self._captured.append(
                        (layer_idx, tensor.detach().cpu())
                    )
            except Exception as exc:  # noqa: BLE001
                log.debug(
                    "Hook on layer %d failed to capture output: %s",
                    layer_idx,
                    exc,
                )

        return _hook

    @staticmethod
    def _extract_hidden_state(output: Any) -> torch.Tensor | None:
        """Extract the hidden-state tensor from a layer's forward output.

        Transformer decoder layers typically return either:
        - A tuple/list where the first element is the hidden state.
        - A ``BaseModelOutput``-like object with a ``.last_hidden_state``
          or indexable ``[0]`` attribute.
        - A bare tensor.
        """
        if isinstance(output, torch.Tensor):
            return output

        if isinstance(output, (tuple, list)) and len(output) > 0:
            candidate = output[0]
            if isinstance(candidate, torch.Tensor):
                return candidate

        # Some model outputs are dataclass-like objects
        if hasattr(output, "last_hidden_state"):
            return output.last_hidden_state

        return None

    @staticmethod
    def _find_transformer_layers(
        model: nn.Module,
    ) -> list[tuple[str, nn.Module]]:
        """Walk the model graph and return transformer decoder layers.

        Returns a list of ``(name, module)`` tuples for every module
        whose class name matches a known transformer layer type.
        """
        layers: list[tuple[str, nn.Module]] = []

        for name, module in model.named_modules():
            cls_name = type(module).__name__

            if cls_name in _KNOWN_LAYER_NAMES:
                layers.append((name, module))
                continue

            # Fallback — check for common substrings
            if any(pattern in cls_name for pattern in _FALLBACK_PATTERNS):
                layers.append((name, module))

        return layers

    def _clear_captured(self) -> None:
        """Free all captured tensors."""
        self._captured.clear()
