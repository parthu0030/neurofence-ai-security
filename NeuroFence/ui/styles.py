"""Centralized stylesheet generator for the NeuroFence dashboard.

Every widget module imports style fragments from here so visual consistency
is maintained from a single source of truth.  All colours and dimensions
derive from ``config.settings.ThemeColors``.
"""

from __future__ import annotations

from config.settings import ThemeColors

_T = ThemeColors()


# ═══════════════════════════════════════════════════════════════════════════
#  Global application stylesheet
# ═══════════════════════════════════════════════════════════════════════════

GLOBAL_STYLESHEET: str = f"""
/* ── Base reset ────────────────────────────────────────────────── */
QMainWindow {{
    background-color: {_T.bg_dark};
}}
QWidget {{
    color: {_T.text_primary};
    font-family: ".AppleSystemUIFont", "Helvetica Neue", Arial;
    font-size: 13px;
}}
QToolTip {{
    background-color: {_T.bg_panel};
    color: {_T.text_primary};
    border: 1px solid {_T.border_light};
    border-radius: 4px;
    padding: 4px 8px;
}}

/* ── Scrollbar ─────────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {_T.border_light};
    min-height: 30px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical:hover {{
    background: {_T.text_muted};
}}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    height: 0;
}}
"""


# ═══════════════════════════════════════════════════════════════════════════
#  Sidebar
# ═══════════════════════════════════════════════════════════════════════════

SIDEBAR_STYLESHEET: str = f"""
/* Sidebar container */
#SidebarFrame {{
    background-color: {_T.bg_darkest};
    border-right: 1px solid {_T.border};
}}

/* Logo area */
#SidebarLogo {{
    color: {_T.accent};
    font-size: 18px;
    font-weight: 700;
    padding: 8px 0;
}}
#SidebarLogoSub {{
    color: {_T.text_muted};
    font-size: 10px;
}}

/* Navigation buttons */
QPushButton#NavButton {{
    text-align: left;
    padding: 10px 16px;
    border: none;
    border-radius: 8px;
    color: {_T.text_secondary};
    font-size: 13px;
    font-weight: 500;
    background: transparent;
}}
QPushButton#NavButton:hover {{
    background-color: {_T.bg_hover};
    color: {_T.text_primary};
}}
QPushButton#NavButtonActive {{
    text-align: left;
    padding: 10px 16px;
    border: none;
    border-radius: 8px;
    color: {_T.accent_light};
    font-size: 13px;
    font-weight: 600;
    background-color: {_T.accent_glow};
}}

/* About button */
QPushButton#AboutButton {{
    text-align: left;
    padding: 10px 16px;
    border: none;
    border-radius: 8px;
    color: {_T.text_muted};
    font-size: 12px;
    background: transparent;
}}
QPushButton#AboutButton:hover {{
    background-color: {_T.bg_hover};
    color: {_T.text_secondary};
}}
"""


# ═══════════════════════════════════════════════════════════════════════════
#  Header
# ═══════════════════════════════════════════════════════════════════════════

HEADER_STYLESHEET: str = f"""
#HeaderFrame {{
    background-color: {_T.bg_darkest};
    border-bottom: 1px solid {_T.border};
}}

#HeaderTitle {{
    color: {_T.text_primary};
    font-size: 16px;
    font-weight: 700;
}}
#HeaderVersion {{
    color: {_T.text_muted};
    font-size: 11px;
    font-weight: 400;
}}
#HeaderStatus {{
    color: {_T.success};
    font-size: 12px;
    font-weight: 500;
}}
#HeaderDateTime {{
    color: {_T.text_secondary};
    font-size: 12px;
}}

/* Search bar */
QLineEdit#SearchBar {{
    background-color: {_T.bg_input};
    border: 1px solid {_T.border};
    border-radius: 8px;
    padding: 6px 12px 6px 32px;
    color: {_T.text_primary};
    font-size: 12px;
    min-width: 240px;
}}
QLineEdit#SearchBar:focus {{
    border-color: {_T.accent};
}}
"""


# ═══════════════════════════════════════════════════════════════════════════
#  Statistic cards
# ═══════════════════════════════════════════════════════════════════════════

CARD_STYLESHEET: str = f"""
#StatCard {{
    background-color: {_T.bg_panel};
    border: 1px solid {_T.border};
    border-radius: 12px;
}}
#StatCardIcon {{
    font-size: 24px;
}}
#StatCardValue {{
    color: {_T.text_primary};
    font-size: 28px;
    font-weight: 700;
}}
#StatCardLabel {{
    color: {_T.text_secondary};
    font-size: 12px;
    font-weight: 500;
}}
"""


# ═══════════════════════════════════════════════════════════════════════════
#  Quick Scan panel
# ═══════════════════════════════════════════════════════════════════════════

QUICK_SCAN_STYLESHEET: str = f"""
#QuickScanCard {{
    background-color: {_T.bg_panel};
    border: 1px solid {_T.border};
    border-radius: 12px;
}}
#QuickScanTitle {{
    color: {_T.text_primary};
    font-size: 16px;
    font-weight: 700;
}}

/* Upload button */
QPushButton#UploadBtn {{
    background-color: {_T.accent};
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 14px 32px;
    font-size: 14px;
    font-weight: 600;
}}
QPushButton#UploadBtn:hover {{
    background-color: {_T.accent_hover};
}}

/* Drop zone */
#DropZone {{
    border: 2px dashed {_T.border_light};
    border-radius: 12px;
    background-color: {_T.bg_panel_alt};
}}
#DropZone:hover {{
    border-color: {_T.accent};
}}
#DropZoneText {{
    color: {_T.text_muted};
    font-size: 12px;
}}

/* Formats label */
#FormatsLabel {{
    color: {_T.text_muted};
    font-size: 11px;
}}
#FormatBadge {{
    background-color: {_T.bg_input};
    color: {_T.text_secondary};
    border-radius: 4px;
    padding: 3px 8px;
    font-size: 11px;
    font-family: "Menlo", "Courier New";
}}

/* Scan button — disabled state */
QPushButton#ScanBtn {{
    background-color: {_T.bg_input};
    color: {_T.text_muted};
    border: 1px solid {_T.border};
    border-radius: 10px;
    padding: 12px 40px;
    font-size: 14px;
    font-weight: 600;
}}
/* Scan button — enabled state */
QPushButton#ScanBtn:enabled {{
    background-color: {_T.success};
    color: #ffffff;
    border: 1px solid {_T.success};
}}
QPushButton#ScanBtn:enabled:hover {{
    background-color: #16a34a;
    border-color: #16a34a;
}}

/* Upload success message */
#SuccessLabel {{
    color: {_T.success};
    font-size: 12px;
    font-weight: 600;
}}
"""


# ═══════════════════════════════════════════════════════════════════════════
#  Recent Activity table
# ═══════════════════════════════════════════════════════════════════════════

ACTIVITY_STYLESHEET: str = f"""
#ActivityCard {{
    background-color: {_T.bg_panel};
    border: 1px solid {_T.border};
    border-radius: 12px;
}}
#ActivityTitle {{
    color: {_T.text_primary};
    font-size: 15px;
    font-weight: 700;
}}

QTableWidget {{
    background-color: transparent;
    border: none;
    gridline-color: {_T.border};
    font-size: 12px;
}}
QTableWidget::item {{
    padding: 8px 12px;
    border-bottom: 1px solid {_T.border};
}}
QTableWidget::item:selected {{
    background-color: {_T.accent_glow};
}}
QHeaderView::section {{
    background-color: {_T.bg_panel_alt};
    color: {_T.text_secondary};
    border: none;
    border-bottom: 1px solid {_T.border};
    padding: 8px 12px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
}}
"""


# ═══════════════════════════════════════════════════════════════════════════
#  Right information panel
# ═══════════════════════════════════════════════════════════════════════════

INFO_PANEL_STYLESHEET: str = f"""
#InfoPanel {{
    background-color: {_T.bg_panel};
    border: 1px solid {_T.border};
    border-radius: 12px;
}}
#InfoPanelTitle {{
    color: {_T.text_primary};
    font-size: 14px;
    font-weight: 700;
}}
#InfoSectionTitle {{
    color: {_T.text_secondary};
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
}}
#InfoKey {{
    color: {_T.text_muted};
    font-size: 12px;
}}
#InfoValue {{
    color: {_T.text_primary};
    font-size: 12px;
    font-weight: 500;
}}
#ModelBadge {{
    background-color: {_T.bg_input};
    color: {_T.accent_light};
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 500;
}}
#StatusDot {{
    color: {_T.success};
    font-size: 10px;
}}
#ModelInfoValue {{
    color: {_T.text_primary};
    font-size: 11px;
    font-weight: 500;
}}
#Sha256Value {{
    color: {_T.accent_light};
    font-size: 10px;
    font-family: "Menlo", "Courier New", monospace;
    font-weight: 400;
}}
"""


# ═══════════════════════════════════════════════════════════════════════════
#  Bottom status bar
# ═══════════════════════════════════════════════════════════════════════════

STATUS_BAR_STYLESHEET: str = f"""
#StatusBarFrame {{
    background-color: {_T.bg_darkest};
    border-top: 1px solid {_T.border};
}}
#StatusBarLabel {{
    color: {_T.text_muted};
    font-size: 11px;
}}
#StatusBarReady {{
    color: {_T.success};
    font-size: 11px;
    font-weight: 500;
}}
"""


# ═══════════════════════════════════════════════════════════════════════════
#  Prompt Engine panel
# ═══════════════════════════════════════════════════════════════════════════

PROMPT_PANEL_STYLESHEET: str = f"""
/* ── Panel container ─────────────────────────────────────────────── */
#PromptPanelContainer {{
    background-color: {_T.bg_dark};
}}

/* ── Section cards ───────────────────────────────────────────────── */
#PromptInputCard, #ResponseCard, #HistoryCard {{
    background-color: {_T.bg_panel};
    border: 1px solid {_T.border};
    border-radius: 12px;
}}

/* ── Section titles ──────────────────────────────────────────────── */
#PromptSectionTitle {{
    color: {_T.text_primary};
    font-size: 15px;
    font-weight: 700;
}}

/* ── Combo boxes ─────────────────────────────────────────────────── */
QComboBox#CategoryCombo, QComboBox#PromptCombo {{
    background-color: {_T.bg_input};
    border: 1px solid {_T.border};
    border-radius: 8px;
    padding: 8px 12px;
    color: {_T.text_primary};
    font-size: 13px;
    min-width: 200px;
}}
QComboBox#CategoryCombo:hover, QComboBox#PromptCombo:hover {{
    border-color: {_T.accent};
}}
QComboBox#CategoryCombo::drop-down, QComboBox#PromptCombo::drop-down {{
    border: none;
    padding-right: 8px;
}}
QComboBox#CategoryCombo QAbstractItemView,
QComboBox#PromptCombo QAbstractItemView {{
    background-color: {_T.bg_panel};
    border: 1px solid {_T.border};
    color: {_T.text_primary};
    selection-background-color: {_T.accent_glow};
    padding: 4px;
}}

/* ── Text editors ────────────────────────────────────────────────── */
QPlainTextEdit#PromptEditor {{
    background-color: {_T.bg_input};
    border: 1px solid {_T.border};
    border-radius: 8px;
    padding: 10px 12px;
    color: {_T.text_primary};
    font-size: 13px;
    font-family: "Menlo", "Courier New", monospace;
}}
QPlainTextEdit#PromptEditor:focus {{
    border-color: {_T.accent};
}}

QPlainTextEdit#ResponseDisplay {{
    background-color: {_T.bg_input};
    border: 1px solid {_T.border};
    border-radius: 8px;
    padding: 10px 12px;
    color: {_T.text_primary};
    font-size: 13px;
    font-family: "Menlo", "Courier New", monospace;
}}

/* ── Character counter ───────────────────────────────────────────── */
#CharCounter {{
    color: {_T.text_muted};
    font-size: 11px;
    font-family: "Menlo", "Courier New", monospace;
}}
#CharCounterWarn {{
    color: {_T.warning};
    font-size: 11px;
    font-family: "Menlo", "Courier New", monospace;
    font-weight: 600;
}}

/* ── Sliders ─────────────────────────────────────────────────────── */
QSlider::groove:horizontal {{
    border: none;
    height: 6px;
    background: {_T.bg_input};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {_T.accent};
    border: none;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}}
QSlider::handle:horizontal:hover {{
    background: {_T.accent_hover};
}}
QSlider::sub-page:horizontal {{
    background: {_T.accent};
    border-radius: 3px;
}}

#SliderLabel {{
    color: {_T.text_secondary};
    font-size: 12px;
    font-weight: 500;
}}
#SliderValue {{
    color: {_T.accent_light};
    font-size: 12px;
    font-weight: 600;
    font-family: "Menlo", "Courier New", monospace;
}}

/* ── Run button ──────────────────────────────────────────────────── */
QPushButton#RunPromptBtn {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {_T.accent}, stop:1 {_T.accent_light}
    );
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 14px 48px;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.5px;
}}
QPushButton#RunPromptBtn:hover {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {_T.accent_hover}, stop:1 {_T.accent}
    );
}}
QPushButton#RunPromptBtn:disabled {{
    background-color: {_T.bg_input};
    color: {_T.text_muted};
    border: 1px solid {_T.border};
}}

/* ── Statistics grid ─────────────────────────────────────────────── */
#StatBox {{
    background-color: {_T.bg_panel_alt};
    border: 1px solid {_T.border};
    border-radius: 8px;
}}
#StatLabel {{
    color: {_T.text_muted};
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
#StatValue {{
    color: {_T.text_primary};
    font-size: 16px;
    font-weight: 700;
}}
#StatValueAccent {{
    color: {_T.accent_light};
    font-size: 16px;
    font-weight: 700;
}}
#StatusSuccess {{
    color: {_T.success};
    font-size: 14px;
    font-weight: 700;
}}
#StatusError {{
    color: {_T.danger};
    font-size: 14px;
    font-weight: 700;
}}

/* ── History table ───────────────────────────────────────────────── */
#HistoryCard QTableWidget {{
    background-color: transparent;
    border: none;
    gridline-color: {_T.border};
    font-size: 12px;
}}
#HistoryCard QTableWidget::item {{
    padding: 8px 12px;
    border-bottom: 1px solid {_T.border};
}}
#HistoryCard QTableWidget::item:selected {{
    background-color: {_T.accent_glow};
}}
#HistoryCard QHeaderView::section {{
    background-color: {_T.bg_panel_alt};
    color: {_T.text_secondary};
    border: none;
    border-bottom: 1px solid {_T.border};
    padding: 8px 12px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
}}

/* ── Running indicator ───────────────────────────────────────────── */
#RunningLabel {{
    color: {_T.accent_light};
    font-size: 13px;
    font-weight: 600;
}}
"""


# ═══════════════════════════════════════════════════════════════════════════
#  Activation Tracking panel
# ═══════════════════════════════════════════════════════════════════════════

ACTIVATION_PANEL_STYLESHEET: str = f"""
/* ── Panel container ─────────────────────────────────────────────── */
#ActivationPanelContainer {{
    background-color: {_T.bg_dark};
}}

/* ── Section cards ───────────────────────────────────────────────── */
#ActivationStatusCard, #LayerTableCard, #ActivationChartCard {{
    background-color: {_T.bg_panel};
    border: 1px solid {_T.border};
    border-radius: 12px;
}}

/* ── Section titles ──────────────────────────────────────────────── */
#ActivationSectionTitle {{
    color: {_T.text_primary};
    font-size: 15px;
    font-weight: 700;
}}

/* ── Status boxes ────────────────────────────────────────────────── */
#ActivationStatBox {{
    background-color: {_T.bg_panel_alt};
    border: 1px solid {_T.border};
    border-radius: 8px;
}}
#ActivationStatLabel {{
    color: {_T.text_muted};
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
#ActivationStatValue {{
    color: {_T.text_primary};
    font-size: 16px;
    font-weight: 700;
}}
#ActivationStatusSuccess {{
    color: {_T.success};
    font-size: 14px;
    font-weight: 700;
}}
#ActivationStatusError {{
    color: {_T.danger};
    font-size: 14px;
    font-weight: 700;
}}

/* ── Layer statistics table ──────────────────────────────────────── */
#LayerTableCard QTableWidget {{
    background-color: transparent;
    border: none;
    gridline-color: {_T.border};
    font-size: 12px;
}}
#LayerTableCard QTableWidget::item {{
    padding: 8px 12px;
    border-bottom: 1px solid {_T.border};
}}
#LayerTableCard QTableWidget::item:selected {{
    background-color: {_T.accent_glow};
}}
#LayerTableCard QHeaderView::section {{
    background-color: {_T.bg_panel_alt};
    color: {_T.text_secondary};
    border: none;
    border-bottom: 1px solid {_T.border};
    padding: 8px 12px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
}}
"""


