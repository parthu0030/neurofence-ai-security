"""Compute-device detection for NeuroFence.

Probes the runtime for the best available accelerator and exposes
a simple :class:`DeviceInfo` dataclass so callers never hard-code
device strings.

Priority order: **CUDA → MPS (Apple Silicon) → CPU**
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import torch

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class DeviceInfo:
    """Describes the compute device selected for model loading.

    Attributes:
        device_name: Torch device string — ``"cuda"``, ``"mps"``, or ``"cpu"``.
        device_type: Human-readable label — ``"CUDA"``, ``"MPS"``, or ``"CPU"``.
        is_gpu:      ``True`` when a hardware accelerator is available.
    """

    device_name: str
    device_type: str
    is_gpu: bool


def detect_device() -> DeviceInfo:
    """Return a :class:`DeviceInfo` for the best available device.

    The function checks CUDA first, then Apple Silicon MPS, and
    falls back to CPU.
    """
    if torch.cuda.is_available():
        info = DeviceInfo(device_name="cuda", device_type="CUDA", is_gpu=True)
        log.info("Device detected: CUDA (%s)", torch.cuda.get_device_name(0))
        return info

    if torch.backends.mps.is_available():
        info = DeviceInfo(device_name="mps", device_type="MPS", is_gpu=True)
        log.info("Device detected: MPS (Apple Silicon)")
        return info

    log.info("Device detected: CPU (no GPU accelerator found)")
    return DeviceInfo(device_name="cpu", device_type="CPU", is_gpu=False)
