"""
UI Configuration with environment-based profiles and theme management.

Supports 'dev' and 'prod' environments with customizable themes, colors, and window settings.
"""
from dataclasses import dataclass
from typing import Dict


@dataclass
class ColorPalette:
    """Defines colors for the application theme."""
    # Primary background colors
    main_bg: str = "#fff7ec"
    card_bg: str = "rgba(255, 252, 246, 228)"
    stat_card_bg: str = "rgba(255, 247, 232, 0.98)"
    
    # Text colors
    text_primary: str = "#5a2800"
    text_secondary: str = "#a9651d"
    text_dark: str = "#7a3200"
    
    # Accent colors
    border_primary: str = "rgba(227, 166, 66, 0.28)"
    border_light: str = "rgba(230, 177, 94, 0.42)"
    accent_orange: str = "#ffd08a"
    accent_dark: str = "#e68700"
    
    # Status colors
    pending_bg: str = "rgba(255, 243, 224, 0.98)"
    done_bg: str = "rgba(246, 242, 225, 0.98)"
    alert_bg: str = "rgba(255, 235, 219, 0.98)"
    focus_bg: str = "rgba(255, 249, 238, 0.98)"
    money_bg: str = "rgba(255, 245, 226, 0.98)"
    expense_bg: str = "rgba(255, 238, 224, 0.98)"
    credit_bg: str = "rgba(255, 241, 229, 0.98)"
    owe_bg: str = "rgba(245, 243, 230, 0.98)"
    
    # Priority colors
    priority_high: str = "#ffe0c1"
    priority_high_text: str = "#9c3f00"
    priority_medium: str = "#fff1d0"
    priority_medium_text: str = "#8b5a00"
    priority_low: str = "#f5f0df"
    priority_low_text: str = "#6e6a2d"
    
    # Button colors
    button_bg: str = "rgba(255, 253, 249, 0.95)"
    button_hover: str = "#fff0d7"
    button_pressed: str = "#f7d29c"
    button_disabled: str = "#f2dfc2"
    button_disabled_border: str = "#ead3b0"
    
    # Input colors
    input_bg: str = "rgba(255, 255, 255, 0.95)"
    input_text: str = "#4f2200"
    input_border: str = "#efc57f"
    input_focus_border: str = "#e68700"
    
    # Combo box popup
    popup_bg: str = "#fff9f2"
    popup_text: str = "#6b2a00"
    popup_hover: str = "#fff0d7"
    popup_selected_bg: str = "#f1a33a"
    popup_selected_text: str = "#fffdf9"


@dataclass
class FontConfig:
    """Defines font settings."""
    family: str = "System"
    
    # Font sizes
    size_tiny: int = 10
    size_small: int = 11
    size_base: int = 13
    size_medium: int = 14
    size_large: int = 15
    size_xlarge: int = 16
    size_title: int = 20
    size_page_title: int = 24


@dataclass
class WindowConfig:
    """Defines window dimensions and layout."""
    width: int = 900
    height: int = 700
    min_width: int = 700
    min_height: int = 500
    
    # Layout spacing
    padding_xl: int = 20
    padding_lg: int = 16
    padding_md: int = 14
    padding_sm: int = 10
    padding_xs: int = 8
    
    spacing_lg: int = 12
    spacing_md: int = 10
    spacing_sm: int = 6
    
    # Border radius
    radius_lg: int = 24
    radius_md: int = 18
    radius_sm: int = 14
    radius_xs: int = 10


@dataclass
class UITheme:
    """Complete UI theme configuration."""
    colors: ColorPalette
    fonts: FontConfig
    window: WindowConfig
    
    # Theme name
    name: str = "default"
    debug_mode: bool = False


def create_prod_theme() -> UITheme:
    """Create production environment theme (polished, optimized)."""
    return UITheme(
        colors=ColorPalette(),
        fonts=FontConfig(),
        window=WindowConfig(width=900, height=700),
        name="prod",
        debug_mode=False,
    )


def create_dev_theme() -> UITheme:
    """Create development environment theme (enhanced visibility for debugging)."""
    colors = ColorPalette()
    window = WindowConfig(width=1000, height=800, min_width=800, min_height=600)
    
    return UITheme(
        colors=colors,
        fonts=FontConfig(),
        window=window,
        name="dev",
        debug_mode=True,
    )


def create_high_contrast_theme() -> UITheme:
    """Alternative high-contrast theme for accessibility."""
    colors = ColorPalette(
        main_bg="#f5f0e8",
        text_primary="#2a1800",
        text_dark="#1a0900",
        accent_orange="#ff9900",
        accent_dark="#cc6600",
    )
    return UITheme(
        colors=colors,
        fonts=FontConfig(),
        window=WindowConfig(),
        name="high_contrast",
        debug_mode=False,
    )


class ThemeManager:
    """Manages theme selection and application."""
    
    _themes: Dict[str, UITheme] = {
        "prod": create_prod_theme(),
        "dev": create_dev_theme(),
        "high_contrast": create_high_contrast_theme(),
    }
    
    _current_theme: UITheme = None
    
    @classmethod
    def set_theme(cls, theme_name: str) -> None:
        """Set the active theme."""
        if theme_name not in cls._themes:
            raise ValueError(f"Unknown theme: {theme_name}. Available: {list(cls._themes.keys())}")
        cls._current_theme = cls._themes[theme_name]
    
    @classmethod
    def get_theme(cls) -> UITheme:
        """Get the current active theme."""
        if cls._current_theme is None:
            cls._current_theme = cls._themes["prod"]
        return cls._current_theme
    
    @classmethod
    def register_custom_theme(cls, name: str, theme: UITheme) -> None:
        """Register a custom theme."""
        cls._themes[name] = theme
    
    @classmethod
    def available_themes(cls) -> list[str]:
        """List available theme names."""
        return list(cls._themes.keys())


# Convenience function to get current theme
def get_theme() -> UITheme:
    """Get the currently active UI theme."""
    return ThemeManager.get_theme()


def get_colors() -> ColorPalette:
    """Get the current color palette."""
    return ThemeManager.get_theme().colors


def get_fonts() -> FontConfig:
    """Get the current font configuration."""
    return ThemeManager.get_theme().fonts


def get_window() -> WindowConfig:
    """Get the current window configuration."""
    return ThemeManager.get_theme().window


def generate_stylesheet(theme: UITheme = None) -> str:
    """Generate QSS stylesheet from the current theme."""
    if theme is None:
        theme = get_theme()
    
    c = theme.colors
    
    return f"""
QMainWindow {{
    background: {c.main_bg};
}}
QWidget#navigationBar {{
    background-color: #faf3e6;
    border-right: 1px solid {c.border_primary};
}}
QLabel#navTitle {{
    color: {c.text_dark};
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 0.5px;
}}
QPushButton#navButton {{
    background-color: transparent;
    color: {c.text_primary};
    border: none;
    border-radius: 8px;
    padding: 8px 12px;
    margin: 0 8px;
    font-size: 13px;
    font-weight: 600;
    text-align: left;
}}
QPushButton#navButton:hover {{
    background-color: rgba(255, 208, 138, 0.3);
    color: {c.text_dark};
}}
QPushButton#navButton:pressed {{
    background-color: rgba(255, 208, 138, 0.5);
}}
QPushButton#navButton[active="true"] {{
    background-color: {c.accent_orange};
    color: #6b2a00;
    font-weight: 700;
}}
QPushButton#navButton[active="true"]:hover {{
    background-color: #ffc56a;
}}
QPushButton#aiStatusButton {{
    border-radius: 10px;
    margin: 0 12px;
    padding: 8px 10px;
    min-height: 34px;
    color: white;
    font-size: 12px;
    font-weight: 700;
}}
QPushButton#aiStatusButton[connected="true"] {{
    background-color: #1f9d55;
    border: 1px solid #15703c;
}}
QPushButton#aiStatusButton[connected="false"] {{
    background-color: #d64545;
    border: 1px solid #9f2f2f;
}}
QStackedWidget {{
    background: transparent;
}}
QWidget#infinityPage {{
    background: transparent;
}}
QFrame#pageCard {{
    background-color: {c.card_bg};
    border: 1px solid {c.border_primary};
    border-radius: 24px;
}}
QFrame#statCard {{
    background-color: {c.stat_card_bg};
    border: 1px solid {c.border_light};
    border-radius: 16px;
}}
QFrame#statCard[tone="pending"] {{
    background-color: {c.pending_bg};
}}
QFrame#statCard[tone="done"] {{
    background-color: {c.done_bg};
}}
QFrame#statCard[tone="alert"] {{
    background-color: {c.alert_bg};
}}
QFrame#statCard[tone="focus"] {{
    background-color: {c.focus_bg};
}}
QFrame#statCard[tone="money"] {{
    background-color: {c.money_bg};
}}
QFrame#statCard[tone="expense"] {{
    background-color: {c.expense_bg};
}}
QFrame#statCard[tone="credit"] {{
    background-color: {c.credit_bg};
}}
QFrame#statCard[tone="owe"] {{
    background-color: {c.owe_bg};
}}
QLabel {{
    color: {c.text_primary};
    font-size: 13px;
}}
QLabel#pageTitle {{
    color: {c.text_dark};
    font-size: 24px;
    font-weight: 700;
    letter-spacing: 0.5px;
}}
QLabel#pageSubtitle {{
    color: {c.text_secondary};
    font-size: 13px;
}}
QLabel#sectionTitle {{
    color: #b45b00;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}}
QLabel#detailValue {{
    color: #6d2f00;
    font-size: 14px;
    font-weight: 600;
}}
QLabel#statValue {{
    color: {c.text_dark};
    font-size: 20px;
    font-weight: 700;
}}
QLabel#statCaption {{
    color: #b45b00;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.8px;
}}
QLabel#insightHeading,
QLabel#focusTitle,
QLabel#emptyStateTitle,
QLabel#taskTitle {{
    color: {c.text_dark};
    font-size: 15px;
    font-weight: 700;
}}
QLabel#insightText,
QLabel#focusBody,
QLabel#emptyStateBody,
QLabel#taskBody {{
    color: #6f4419;
    font-size: 13px;
}}
QLabel#focusMeta,
QLabel#taskMeta {{
    color: #b16a22;
    font-size: 11px;
}}
QLabel#priorityBadge {{
    border-radius: 10px;
    padding: 3px 8px;
    font-size: 10px;
    font-weight: 700;
}}
QLabel#priorityBadge[priority="High"] {{
    background-color: {c.priority_high};
    color: {c.priority_high_text};
}}
QLabel#priorityBadge[priority="Medium"] {{
    background-color: {c.priority_medium};
    color: {c.priority_medium_text};
}}
QLabel#priorityBadge[priority="Low"] {{
    background-color: {c.priority_low};
    color: {c.priority_low_text};
}}
QLabel#monthLabel {{
    color: {c.text_dark};
    font-size: 16px;
    font-weight: 700;
}}
QLabel#entryTypeBadge {{
    border-radius: 10px;
    padding: 3px 8px;
    font-size: 10px;
    font-weight: 700;
    background-color: #fff0d0;
    color: #8a5a00;
}}
QLabel#entryAmount {{
    font-size: 15px;
    font-weight: 700;
}}
QLabel#entryAmount[direction="positive"] {{
    color: {c.text_dark};
}}
QLabel#entryAmount[direction="negative"] {{
    color: #9a4300;
}}
QLabel#entryTitle {{
    color: {c.text_dark};
    font-size: 14px;
    font-weight: 700;
}}
QLabel#entryMeta {{
    color: #b16a22;
    font-size: 11px;
}}
QLabel#fieldLabel {{
    color: {c.text_dark};
    font-size: 12px;
    font-weight: 600;
}}
QPushButton {{
    min-height: 36px;
    padding: 0 14px;
    border-radius: 12px;
    border: 1px solid {c.border_primary};
    background-color: {c.button_bg};
    color: {c.text_dark};
    font-size: 13px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: {c.button_hover};
}}
QPushButton:pressed {{
    background-color: {c.button_pressed};
}}
QPushButton#primaryButton {{
    background-color: {c.accent_orange};
    border: 2px solid {c.accent_dark};
    color: {c.text_dark};
    font-weight: 700;
}}
QPushButton#primaryButton:hover {{
    background-color: #ffc56a;
}}
QPushButton#primaryButton:pressed {{
    background-color: #f2b453;
}}
QPushButton#secondaryButton {{
    background-color: rgba(255, 245, 230, 0.98);
}}
QPushButton#ghostButton {{
    background-color: rgba(255, 255, 255, 0.55);
    border: 1px solid rgba(230, 161, 58, 0.38);
}}
QPushButton#compactButton,
QPushButton#compactPrimaryButton,
QPushButton#compactDangerButton,
QPushButton#filterChip {{
    min-height: 30px;
    padding: 0 12px;
    border-radius: 10px;
    font-size: 12px;
}}
QPushButton#compactPrimaryButton {{
    background-color: {c.accent_orange};
    border: 2px solid {c.accent_dark};
    color: {c.text_dark};
    font-weight: 700;
}}
QPushButton#compactPrimaryButton:hover {{
    background-color: #ffc56a;
}}
QPushButton#compactDangerButton {{
    background-color: #fff0e1;
    border: 1px solid #f0b173;
    color: #9a4300;
}}
QPushButton#compactDangerButton:hover {{
    background-color: #ffdcbc;
}}
QPushButton#filterChip {{
    background-color: rgba(255, 250, 241, 0.95);
    border: 1px solid rgba(230, 161, 58, 0.45);
}}
QPushButton#filterChip:checked {{
    background-color: {c.accent_orange};
    border: 2px solid {c.accent_dark};
    color: {c.text_dark};
    font-weight: 700;
}}
QPushButton:disabled {{
    background-color: {c.button_disabled};
    border-color: {c.button_disabled_border};
    color: #b58b5d;
}}
QLineEdit,
QTextEdit,
QListWidget,
QComboBox,
QSpinBox,
QDoubleSpinBox {{
    background-color: {c.input_bg};
    color: {c.input_text};
    border: 1px solid {c.input_border};
    border-radius: 14px;
    padding: 8px 10px;
    selection-background-color: #f1a33a;
    selection-color: white;
}}
QComboBox {{
    padding-right: 30px;
}}
QLineEdit:focus,
QTextEdit:focus,
QListWidget:focus,
QComboBox:focus,
QSpinBox:focus,
QDoubleSpinBox:focus {{
    border: 2px solid {c.input_focus_border};
}}
QTextEdit#chatHistory {{
    background-color: rgba(255, 253, 249, 0.98);
    border: 1px solid rgba(230, 161, 58, 0.38);
    border-radius: 18px;
    padding: 10px 12px;
}}
QLineEdit#chatInput {{
    min-height: 38px;
}}
QListWidget {{
    outline: 0;
}}
QListWidget#cardList {{
    padding: 2px 0;
}}
QListWidget#cardList::item {{
    margin: 0;
    padding: 0;
    border-radius: 10px;
    color: {c.text_primary};
}}
QListWidget#cardList::item:hover {{
    background-color: #fff1d8;
}}
QListWidget#cardList::item:selected {{
    background-color: #ffe0b3;
    color: #6b2a00;
}}
QComboBox::drop-down {{
    border: none;
    width: 26px;
}}
QFrame#insightCard,
QFrame#focusCard,
QFrame#emptyStateCard,
QFrame#taskCard,
QFrame#moneyEntryCard {{
    background-color: rgba(255, 251, 244, 0.94);
    border: 1px solid rgba(232, 177, 86, 0.42);
    border-radius: 18px;
}}
QFrame#focusCard {{
    background-color: {c.focus_bg};
}}
QFrame#taskCard[selected="true"] {{
    background-color: #fff0d8;
    border: 2px solid {c.accent_dark};
}}
QFrame#emptyStateCard {{
    background-color: rgba(255, 248, 236, 0.98);
}}
QFrame#moneyEntryCard {{
    background-color: rgba(255, 250, 242, 0.98);
}}
QMessageBox {{
    background-color: #fff9f0;
}}
"""


def generate_combo_popup_stylesheet(theme: UITheme = None) -> str:
    """Generate QSS stylesheet for combo box popups."""
    if theme is None:
        theme = get_theme()
    
    c = theme.colors
    
    return f"""
QListView {{
    background-color: {c.popup_bg};
    color: {c.popup_text};
    border: 1px solid {c.input_border};
    border-radius: 12px;
    outline: 0;
    padding: 6px;
}}
QListView::item {{
    min-height: 30px;
    margin: 2px 4px;
    padding: 6px 10px;
    border-radius: 8px;
    color: {c.popup_text};
}}
QListView::item:hover {{
    background-color: {c.popup_hover};
    color: {c.text_dark};
}}
QListView::item:selected {{
    background-color: {c.popup_selected_bg};
    color: {c.popup_selected_text};
}}
"""
