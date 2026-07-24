"""Matplotlib-based scan history charts for NeuroFence AI Security.

Embeds a 2×2 grid of history trend charts inside a PyQt6 widget:
    1. Security Score Trend    — Line chart of security scores over time
    2. Findings Trend          — Stacked bar chart of findings per scan by severity
    3. Scan Timeline           — Timeline scatter of scan events and statuses
    4. Average Activation Trend — Dual line plot of average and peak activation values
"""

from __future__ import annotations

import logging
from typing import Any

import matplotlib
matplotlib.use("QtAgg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt6.QtWidgets import QVBoxLayout, QWidget

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


class HistoryChartWidget(QWidget):
    """A 2×2 matplotlib chart grid showing multi-scan history trends."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._figure = Figure(figsize=(11, 7), dpi=100, facecolor=_BG_DARK)
        self._canvas = FigureCanvas(self._figure)
        self._canvas.setStyleSheet(f"background-color: {_BG_DARK};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._canvas)

        self._draw_placeholder()

    def update_charts(self, scans: list[dict[str, Any]]) -> None:
        """Redraw all four history trend subplots with data from *scans*."""
        if not scans:
            self._draw_placeholder()
            return

        # Scans are ordered newest first from DB; reverse for chronological plotting
        chrono_scans = list(reversed(scans))

        self._figure.clear()
        x_indices = np.arange(len(chrono_scans))
        labels = [f"Scan #{s.get('id', i+1)}" for i, s in enumerate(chrono_scans)]

        # ── 1. Security Score Trend ───────────────────────────────────
        ax1 = self._figure.add_subplot(2, 2, 1)
        scores = [float(s.get("security_score", 0.0)) for s in chrono_scans]
        ax1.plot(x_indices, scores, color=_ACCENT_LIGHT, marker="o", linewidth=2.5, markersize=6)
        ax1.axhline(y=80, color=_SUCCESS, linestyle="--", alpha=0.6, label="Safe Threshold (80)")
        ax1.axhline(y=50, color=_WARNING, linestyle="--", alpha=0.6, label="Risk Threshold (50)")
        ax1.set_ylim(0, 105)
        self._style_axis(ax1, "Security Score Trend", x_indices, labels)
        ax1.set_ylabel("Score (0-100)", color=_TEXT_SECONDARY, fontsize=9)
        ax1.legend(fontsize=8, facecolor=_BG_PANEL, edgecolor=_TEXT_SECONDARY, labelcolor=_TEXT_PRIMARY, loc="lower right")

        # ── 2. Findings Trend (Stacked Bar Chart) ─────────────────────
        ax2 = self._figure.add_subplot(2, 2, 2)
        criticals = [int(s.get("critical_count", 0)) for s in chrono_scans]
        highs = [int(s.get("high_count", 0)) for s in chrono_scans]
        mediums = [int(s.get("medium_count", 0)) for s in chrono_scans]
        lows = [int(s.get("low_count", 0)) for s in chrono_scans]

        ax2.bar(x_indices, criticals, label="Critical", color=_DANGER, width=0.55)
        ax2.bar(x_indices, highs, bottom=criticals, label="High", color=_WARNING, width=0.55)
        
        bot_med = [c + h for c, h in zip(criticals, highs)]
        ax2.bar(x_indices, mediums, bottom=bot_med, label="Medium", color=_CYAN, width=0.55)

        bot_low = [c + h + m for c, h, m in zip(criticals, highs, mediums)]
        ax2.bar(x_indices, lows, bottom=bot_low, label="Low", color=_SUCCESS, width=0.55)

        self._style_axis(ax2, "Findings Breakdown Trend", x_indices, labels)
        ax2.set_ylabel("Finding Count", color=_TEXT_SECONDARY, fontsize=9)
        ax2.legend(fontsize=8, facecolor=_BG_PANEL, edgecolor=_TEXT_SECONDARY, labelcolor=_TEXT_PRIMARY, loc="upper right")

        # ── 3. Scan Timeline (Date vs Risk Level) ─────────────────────
        ax3 = self._figure.add_subplot(2, 2, 3)
        dates = [str(s.get("scan_date", ""))[:10] for s in chrono_scans]
        status_colors = []
        for s in chrono_scans:
            score = float(s.get("security_score", 0.0))
            if score >= 85:
                status_colors.append(_SUCCESS)
            elif score >= 60:
                status_colors.append(_WARNING)
            else:
                status_colors.append(_DANGER)

        scatter = ax3.scatter(x_indices, scores, c=status_colors, s=120, zorder=3, edgecolors=_TEXT_PRIMARY, linewidths=1.5)
        ax3.plot(x_indices, scores, color=_TEXT_SECONDARY, linestyle=":", alpha=0.5, zorder=2)
        self._style_axis(ax3, "Scan Timeline & Security Rating", x_indices, dates)
        ax3.set_ylabel("Security Score", color=_TEXT_SECONDARY, fontsize=9)

        # ── 4. Average Activation Trend ───────────────────────────────
        ax4 = self._figure.add_subplot(2, 2, 4)
        avg_acts = [float(s.get("average_activation", 0.0)) for s in chrono_scans]
        peak_acts = [float(s.get("peak_activation", 0.0)) for s in chrono_scans]

        ax4.plot(x_indices, avg_acts, color=_CYAN, marker="s", linewidth=2, label="Avg Activation")
        ax4.plot(x_indices, peak_acts, color=_WARNING, marker="^", linewidth=2, linestyle="--", label="Peak Activation")
        self._style_axis(ax4, "Activation Magnitude Trend", x_indices, labels)
        ax4.set_ylabel("Magnitude", color=_TEXT_SECONDARY, fontsize=9)
        ax4.legend(fontsize=8, facecolor=_BG_PANEL, edgecolor=_TEXT_SECONDARY, labelcolor=_TEXT_PRIMARY, loc="upper left")

        self._figure.tight_layout(pad=2.2)
        self._canvas.draw()

    def _draw_placeholder(self) -> None:
        """Draw placeholder message when no scan history exists."""
        self._figure.clear()
        ax = self._figure.add_subplot(1, 1, 1)
        ax.set_facecolor(_BG_DARK)
        ax.text(
            0.5,
            0.5,
            "No scan history available for trend visualization",
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
        ax.set_xticklabels(x_labels, fontsize=8, color=_TEXT_SECONDARY, rotation=30, ha="right")
        ax.tick_params(axis="y", colors=_TEXT_SECONDARY, labelsize=8)
        ax.tick_params(axis="x", colors=_TEXT_SECONDARY)

        for spine in ax.spines.values():
            spine.set_color(_TEXT_SECONDARY)
            spine.set_linewidth(0.5)

        ax.grid(axis="y", color=_TEXT_SECONDARY, alpha=0.15, linewidth=0.5)
