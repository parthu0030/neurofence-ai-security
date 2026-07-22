"""Matplotlib-based activation charts for NeuroFence.

Embeds a 2×2 grid of charts inside a PyQt6 widget using the
``matplotlib.backends.backend_qtagg`` backend.

Charts:
    1. Layer Activity   — L2 norm per layer (bar chart)
    2. Mean Activation  — mean per layer (bar chart)
    3. Std Deviation    — std per layer (bar chart)
    4. Activation Range — min / mean / max grouped bars per layer
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import matplotlib
matplotlib.use("QtAgg")  # noqa: E402 — must be set before importing pyplot

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt6.QtWidgets import QVBoxLayout, QWidget

if TYPE_CHECKING:
    from analysis.activation_statistics import ActivationSummary

log = logging.getLogger(__name__)

# ── NeuroFence dark-theme colours ────────────────────────────────────────
_BG_DARK = "#0b1120"
_BG_PANEL = "#111827"
_TEXT_PRIMARY = "#e5e7eb"
_TEXT_SECONDARY = "#9ca3af"
_ACCENT = "#3b82f6"
_ACCENT_LIGHT = "#60a5fa"
_SUCCESS = "#22c55e"
_WARNING = "#f59e0b"
_DANGER = "#ef4444"
_CYAN = "#06b6d4"


class ActivationChartWidget(QWidget):
    """A 2×2 matplotlib chart grid showing activation statistics.

    Call :meth:`update_charts` after each prompt execution to redraw
    all four subplots.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._figure = Figure(figsize=(10, 7), dpi=100, facecolor=_BG_DARK)
        self._canvas = FigureCanvas(self._figure)
        self._canvas.setStyleSheet(f"background-color: {_BG_DARK};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._canvas)

        # Draw empty placeholders
        self._draw_placeholder()

    # ── Public API ───────────────────────────────────────────────────

    def update_charts(self, summary: ActivationSummary) -> None:
        """Redraw all four charts with data from *summary*.

        Args:
            summary: An :class:`ActivationSummary` containing per-layer
                     statistics.
        """
        if not summary.layers:
            self._draw_placeholder()
            return

        self._figure.clear()

        layers = summary.layers
        x_labels = [f"L{la.layer_number}" for la in layers]
        x = np.arange(len(layers))

        # ── 1. Layer Activity (L2 Norm) ──────────────────────────────
        ax1 = self._figure.add_subplot(2, 2, 1)
        norms = [la.norm for la in layers]
        bars1 = ax1.bar(x, norms, color=_ACCENT, edgecolor="none", width=0.7)
        self._style_axis(ax1, "Layer Activity (L2 Norm)", x, x_labels)
        ax1.set_ylabel("L2 Norm", color=_TEXT_SECONDARY, fontsize=9)

        # ── 2. Mean Activation ───────────────────────────────────────
        ax2 = self._figure.add_subplot(2, 2, 2)
        means = [la.mean for la in layers]
        colors2 = [_SUCCESS if m >= 0 else _DANGER for m in means]
        ax2.bar(x, means, color=colors2, edgecolor="none", width=0.7)
        ax2.axhline(y=0, color=_TEXT_SECONDARY, linewidth=0.5, linestyle="--")
        self._style_axis(ax2, "Mean Activation", x, x_labels)
        ax2.set_ylabel("Mean", color=_TEXT_SECONDARY, fontsize=9)

        # ── 3. Standard Deviation ────────────────────────────────────
        ax3 = self._figure.add_subplot(2, 2, 3)
        stds = [la.std for la in layers]
        ax3.bar(x, stds, color=_WARNING, edgecolor="none", width=0.7)
        self._style_axis(ax3, "Standard Deviation", x, x_labels)
        ax3.set_ylabel("Std Dev", color=_TEXT_SECONDARY, fontsize=9)

        # ── 4. Activation Distribution (min / mean / max) ────────────
        ax4 = self._figure.add_subplot(2, 2, 4)
        width = 0.25
        mins = [la.min for la in layers]
        maxs = [la.max for la in layers]

        ax4.bar(x - width, mins, width, label="Min", color=_DANGER, edgecolor="none")
        ax4.bar(x, means, width, label="Mean", color=_CYAN, edgecolor="none")
        ax4.bar(x + width, maxs, width, label="Max", color=_SUCCESS, edgecolor="none")

        ax4.axhline(y=0, color=_TEXT_SECONDARY, linewidth=0.5, linestyle="--")
        self._style_axis(ax4, "Activation Distribution", x, x_labels)
        ax4.set_ylabel("Value", color=_TEXT_SECONDARY, fontsize=9)
        legend = ax4.legend(
            fontsize=8,
            facecolor=_BG_PANEL,
            edgecolor=_TEXT_SECONDARY,
            labelcolor=_TEXT_PRIMARY,
            loc="upper right",
        )
        legend.get_frame().set_alpha(0.9)

        self._figure.tight_layout(pad=2.0)
        self._canvas.draw()

    # ── Private helpers ──────────────────────────────────────────────

    def _draw_placeholder(self) -> None:
        """Draw a single centred message when no data is available."""
        self._figure.clear()
        ax = self._figure.add_subplot(1, 1, 1)
        ax.set_facecolor(_BG_DARK)
        ax.text(
            0.5,
            0.5,
            "Run a prompt to visualize activations",
            ha="center",
            va="center",
            fontsize=14,
            color=_TEXT_SECONDARY,
            transform=ax.transAxes,
        )
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

        self._figure.tight_layout()
        self._canvas.draw()

    @staticmethod
    def _style_axis(ax, title: str, x, x_labels: list[str]) -> None:
        """Apply the NeuroFence dark theme to a matplotlib axis."""
        ax.set_facecolor(_BG_DARK)
        ax.set_title(title, color=_TEXT_PRIMARY, fontsize=11, fontweight="bold", pad=8)
        ax.set_xticks(x)
        ax.set_xticklabels(x_labels, fontsize=8, color=_TEXT_SECONDARY, rotation=45, ha="right")
        ax.tick_params(axis="y", colors=_TEXT_SECONDARY, labelsize=8)
        ax.tick_params(axis="x", colors=_TEXT_SECONDARY)

        for spine in ax.spines.values():
            spine.set_color(_TEXT_SECONDARY)
            spine.set_linewidth(0.5)

        ax.grid(axis="y", color=_TEXT_SECONDARY, alpha=0.15, linewidth=0.5)
