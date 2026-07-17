"""Application entry point for the NeuroFence AI Security desktop app.

This file initializes the PyQt6 application, applies a professional dark theme,
and opens the main welcome window for Day 1 development.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from config.settings import AppConfig


@dataclass(frozen=True)
class ThemeColors:
    """Centralized UI colors for the application shell."""

    window_background: str = "#0f172a"
    panel_background: str = "#111827"
    text_primary: str = "#e5e7eb"
    text_muted: str = "#9ca3af"
    accent: str = "#38bdf8"


def _create_main_window():
    """Build the main window using PyQt6 imports loaded at runtime."""

    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

    class MainWindow(QMainWindow):
        """Main application window for the initial NeuroFence desktop shell."""

        def __init__(self) -> None:
            super().__init__()
            self._theme = ThemeColors()
            self._build_window()
            self._apply_ui()

        def _build_window(self) -> None:
            self.setWindowTitle(AppConfig.APP_TITLE)
            self.setMinimumSize(AppConfig.WINDOW_MIN_WIDTH, AppConfig.WINDOW_MIN_HEIGHT)

            central_widget = QWidget(self)
            layout = QVBoxLayout(central_widget)
            layout.setContentsMargins(40, 40, 40, 40)
            layout.setSpacing(16)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            title_label = QLabel(AppConfig.APP_TITLE)
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_font = QFont()
            title_font.setPointSize(22)
            title_font.setBold(True)
            title_label.setFont(title_font)

            welcome_label = QLabel("Welcome to NeuroFence AI Security")
            welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            welcome_font = QFont()
            welcome_font.setPointSize(14)
            welcome_font.setWeight(QFont.Weight.Medium)
            welcome_label.setFont(welcome_font)

            subtitle_label = QLabel("Offline AI security workspace initialized for future planning modules.")
            subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            subtitle_font = QFont()
            subtitle_font.setPointSize(10)
            subtitle_label.setFont(subtitle_font)

            for label in (title_label, welcome_label, subtitle_label):
                label.setWordWrap(True)
                layout.addWidget(label)

            self.setCentralWidget(central_widget)
            self._title_label = title_label
            self._welcome_label = welcome_label
            self._subtitle_label = subtitle_label

        def _apply_ui(self) -> None:
            self.setStyleSheet(
                f"""
                QMainWindow {{
                    background-color: {self._theme.window_background};
                }}
                QWidget {{
                    color: {self._theme.text_primary};
                    font-family: Segoe UI, Inter, Arial, sans-serif;
                }}
                QLabel {{
                    color: {self._theme.text_primary};
                }}
                """
            )

            self._title_label.setStyleSheet(f"color: {self._theme.accent};")
            self._welcome_label.setStyleSheet(f"color: {self._theme.text_primary};")
            self._subtitle_label.setStyleSheet(f"color: {self._theme.text_muted};")

    return MainWindow()


def _configure_application(app) -> None:
    """Apply a consistent Fusion-based dark palette."""

    from PyQt6.QtGui import QColor, QPalette
    from PyQt6.QtWidgets import QStyleFactory

    app.setApplicationName(AppConfig.APP_TITLE)
    app.setApplicationDisplayName(AppConfig.APP_TITLE)
    app.setOrganizationName(AppConfig.ORGANIZATION_NAME)
    app.setOrganizationDomain(AppConfig.ORGANIZATION_DOMAIN)
    app.setStyle(QStyleFactory.create("Fusion"))

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#0f172a"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e5e7eb"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#111827"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#1f2937"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#e5e7eb"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#111827"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#e5e7eb"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#111827"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#e5e7eb"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#38bdf8"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#0f172a"))
    app.setPalette(palette)


def main() -> int:
    """Run the NeuroFence desktop application."""

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    _configure_application(app)

    window = _create_main_window()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
