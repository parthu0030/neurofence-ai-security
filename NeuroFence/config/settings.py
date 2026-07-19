"""Application configuration for NeuroFence AI Security.

This file centralizes project-level settings so future modules can share a
single source of truth without hard-coding paths or application metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class AppConfig:
    """Core application settings used by the desktop shell."""

    APP_TITLE: str = "NeuroFence AI Security"
    ORGANIZATION_NAME: str = "NeuroFence"
    ORGANIZATION_DOMAIN: str = "neurofence.local"
    VERSION: str = "1.0"
    WINDOW_WIDTH: int = 1600
    WINDOW_HEIGHT: int = 900
    WINDOW_MIN_WIDTH: int = 1200
    WINDOW_MIN_HEIGHT: int = 700

    # ── Model upload ────────────────────────────────────────────────
    ALLOWED_EXTENSIONS: tuple[str, ...] = (".safetensors", ".bin", ".pt")
    DB_NAME: str = "neurofence.db"


@dataclass(frozen=True)
class ThemeColors:
    """Centralized dark-mode color palette for all UI components."""

    # ── Backgrounds ──────────────────────────────────────────────
    bg_darkest: str = "#080c14"        # Deepest background layer
    bg_dark: str = "#0b1120"           # Main window background
    bg_panel: str = "#111827"          # Panel / card background
    bg_panel_alt: str = "#151d2e"      # Alternate panel background
    bg_input: str = "#1a2236"          # Input / search bar
    bg_hover: str = "#1e293b"          # Sidebar hover state

    # ── Borders ──────────────────────────────────────────────────
    border: str = "#1e293b"            # Default border
    border_light: str = "#2a3550"      # Slightly lighter border

    # ── Text ─────────────────────────────────────────────────────
    text_primary: str = "#e5e7eb"      # Primary text
    text_secondary: str = "#9ca3af"    # Secondary / muted text
    text_muted: str = "#6b7280"        # Very muted text

    # ── Accent ───────────────────────────────────────────────────
    accent: str = "#3b82f6"            # Blue accent
    accent_hover: str = "#2563eb"      # Darker accent on hover
    accent_light: str = "#60a5fa"      # Lighter accent
    accent_glow: str = "rgba(59, 130, 246, 0.15)"  # Subtle glow

    # ── Status ───────────────────────────────────────────────────
    success: str = "#22c55e"           # Green — safe / success
    warning: str = "#f59e0b"           # Amber — warning
    danger: str = "#ef4444"            # Red — threat / danger
    info: str = "#06b6d4"             # Cyan — informational


@dataclass(frozen=True)
class NavItem:
    """Describes a single sidebar navigation entry."""

    icon: str
    label: str
    page_key: str


# Navigation items rendered in the sidebar.
NAV_ITEMS: list[NavItem] = [
    NavItem("🏠", "Dashboard", "dashboard"),
    NavItem("🧠", "Model Scanner", "scanner"),
    NavItem("📂", "Scan History", "history"),
    NavItem("📊", "Analytics", "analytics"),
    NavItem("📄", "Reports", "reports"),
    NavItem("⚙", "Settings", "settings"),
]


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
