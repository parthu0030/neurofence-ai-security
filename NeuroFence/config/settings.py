"""Application configuration for NeuroFence AI Security.

This file centralizes project-level settings so future modules can share a
single source of truth without hard-coding paths or application metadata.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class AppConfig:
    """Core application settings used by the desktop shell."""

    APP_TITLE: str = "NeuroFence AI Security"
    ORGANIZATION_NAME: str = "NeuroFence"
    ORGANIZATION_DOMAIN: str = "neurofence.local"
    VERSION: str = "0.1.0"
    WINDOW_MIN_WIDTH: int = 960
    WINDOW_MIN_HEIGHT: int = 640


@dataclass(frozen=True)
class Paths:
    """Resolved project directories for future modules."""

    ROOT: Path = PROJECT_ROOT
    ASSETS: Path = PROJECT_ROOT / "assets"
    ICONS: Path = PROJECT_ROOT / "assets" / "icons"
    IMAGES: Path = PROJECT_ROOT / "assets" / "images"
    CONFIG: Path = PROJECT_ROOT / "config"
    MODELS: Path = PROJECT_ROOT / "models"
    UPLOADS: Path = PROJECT_ROOT / "uploads"
    SCANNER: Path = PROJECT_ROOT / "scanner"
    UI: Path = PROJECT_ROOT / "ui"
    DATABASE: Path = PROJECT_ROOT / "database"
    REPORTS: Path = PROJECT_ROOT / "reports"
    LOGS: Path = PROJECT_ROOT / "logs"
    UTILS: Path = PROJECT_ROOT / "utils"
    TESTS: Path = PROJECT_ROOT / "tests"
