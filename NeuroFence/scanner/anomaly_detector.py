"""Activation anomaly detector for NeuroFence.

Step 6 of the NeuroFence Security Pipeline.

Analyzes hidden-state activation statistics captured across transformer layers
for statistical anomalies, Z-score outliers, activation saturation, and representation collapse.

This module contains **no UI code** — it is pure business logic.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from analysis.activation_statistics import ActivationSummary, LayerActivation


@dataclass(frozen=True)
class ActivationAnomaly:
    """Represents a statistical anomaly detected in a transformer layer's activation.

    Attributes:
        layer_number: Zero-based index of the transformer layer.
        anomaly_type: Category label ("Layer Norm Spike", "Activation Saturation",
                      "Early Layer Perturbation", "Representation Collapse").
        severity:     Severity level ("Critical", "High", "Medium", "Low").
        z_score:      Standardized deviation score (Z-score) of the activation norm.
        description:  Detailed description of the detected anomaly.
    """

    layer_number: int
    anomaly_type: str
    severity: str
    z_score: float
    description: str


class AnomalyDetector:
    """Detects statistical anomalies across layer-wise activation summaries."""

    def __init__(self, z_threshold: float = 2.5) -> None:
        """Initialize the anomaly detector.

        Args:
            z_threshold: Z-score cutoff beyond which a layer norm is flagged as anomalous.
        """
        self.z_threshold = z_threshold

    def detect(self, summary: ActivationSummary | None) -> list[ActivationAnomaly]:
        """Analyze *summary* for layer-level activation anomalies.

        Args:
            summary: An :class:`ActivationSummary` produced by ``ActivationTrackerService``.

        Returns:
            A list of :class:`ActivationAnomaly` instances ordered by layer index.
        """
        if summary is None or not summary.layers:
            return []

        layers = summary.layers
        num_layers = len(layers)
        anomalies: list[ActivationAnomaly] = []

        # ── 1. Calculate population statistics for L2 norms ───────────
        norms = [layer.norm for layer in layers]
        mean_norm = sum(norms) / num_layers
        variance = sum((x - mean_norm) ** 2 for x in norms) / num_layers
        std_norm = math.sqrt(variance) if variance > 0 else 1e-6

        # ── 2. Layer-by-layer Z-score evaluation ──────────────────────
        for idx, layer in enumerate(layers):
            z_score = (layer.norm - mean_norm) / std_norm

            # Norm Spike Outlier (> Z threshold)
            if z_score > self.z_threshold:
                severity = "Critical" if z_score > 3.5 else "High"
                anomalies.append(
                    ActivationAnomaly(
                        layer_number=layer.layer_number,
                        anomaly_type="Layer Norm Spike",
                        severity=severity,
                        z_score=round(z_score, 2),
                        description=(
                            f"Layer {layer.layer_number} activation norm ({layer.norm:.2f}) "
                            f"is {z_score:.2f}σ above the cross-layer mean ({mean_norm:.2f})."
                        ),
                    )
                )

            # Early Layer Perturbation (First 25% of layers showing high norm)
            if idx < max(1, num_layers // 4) and z_score > 1.8:
                anomalies.append(
                    ActivationAnomaly(
                        layer_number=layer.layer_number,
                        anomaly_type="Early Layer Perturbation",
                        severity="Medium",
                        z_score=round(z_score, 2),
                        description=(
                            f"Early layer {layer.layer_number} exhibits elevated activation "
                            f"intensity ({layer.norm:.2f}), suggesting adversarial prompt noise."
                        ),
                    )
                )

            # Activation Saturation (Extreme peak values relative to std)
            if layer.std > 0 and (layer.max / (layer.std + 1e-6)) > 15.0:
                anomalies.append(
                    ActivationAnomaly(
                        layer_number=layer.layer_number,
                        anomaly_type="Activation Saturation",
                        severity="High",
                        z_score=round(z_score, 2),
                        description=(
                            f"Layer {layer.layer_number} has an extreme peak value ({layer.max:.2f}) "
                            f"relative to layer std ({layer.std:.4f})."
                        ),
                    )
                )

        # ── 3. Check for Representation Collapse ───────────────────────
        # If overall average activation is near zero across deep layers
        deep_layers = layers[int(num_layers * 0.75) :]
        if deep_layers:
            deep_mean = sum(l.mean for l in deep_layers) / len(deep_layers)
            if abs(deep_mean) < 1e-5:
                anomalies.append(
                    ActivationAnomaly(
                        layer_number=deep_layers[0].layer_number,
                        anomaly_type="Representation Collapse",
                        severity="High",
                        z_score=0.0,
                        description=(
                            f"Deep layers (layers {deep_layers[0].layer_number} to {deep_layers[-1].layer_number}) "
                            f"exhibit near-zero mean activation ({deep_mean:.6f}), indicating representation collapse."
                        ),
                    )
                )

        return anomalies
