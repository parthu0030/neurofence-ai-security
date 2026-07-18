"""Application entry point for NeuroFence AI Security — Day 2.

Initialises the PyQt6 application, applies the Fusion dark palette,
and launches the professional dashboard window.

Run:
    python app.py
"""

from __future__ import annotations

import sys

from config.settings import AppConfig


def _configure_application(app) -> None:
    """Apply a consistent Fusion-based dark palette to the QApplication."""

    from PyQt6.QtGui import QColor, QPalette
    from PyQt6.QtWidgets import QStyleFactory

    app.setApplicationName(AppConfig.APP_TITLE)
    app.setApplicationDisplayName(AppConfig.APP_TITLE)
    app.setOrganizationName(AppConfig.ORGANIZATION_NAME)
    app.setOrganizationDomain(AppConfig.ORGANIZATION_DOMAIN)
    app.setStyle(QStyleFactory.create("Fusion"))

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#0b1120"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e5e7eb"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#111827"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#1f2937"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#e5e7eb"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#111827"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#e5e7eb"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#111827"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#e5e7eb"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#3b82f6"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#0b1120"))
    app.setPalette(palette)


def main() -> int:
    """Run the NeuroFence desktop application."""

    from PyQt6.QtWidgets import QApplication, QMainWindow

    from ui.dashboard import DashboardWindow
    from ui.styles import GLOBAL_STYLESHEET

    app = QApplication(sys.argv)
    _configure_application(app)
    app.setStyleSheet(GLOBAL_STYLESHEET)

    # ── Main window ──────────────────────────────────────────────
    window = QMainWindow()
    window.setWindowTitle(AppConfig.APP_TITLE)
    window.resize(AppConfig.WINDOW_WIDTH, AppConfig.WINDOW_HEIGHT)
    window.setMinimumSize(AppConfig.WINDOW_MIN_WIDTH, AppConfig.WINDOW_MIN_HEIGHT)

    dashboard = DashboardWindow()
    window.setCentralWidget(dashboard)

    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
