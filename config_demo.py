#!/usr/bin/env python3
"""
Configuration System Demo
Demonstrates how to use the new UI configuration system.
"""

from app.ui_config import (
    ThemeManager,
    get_theme,
    get_colors,
    get_fonts,
    get_window,
    generate_stylesheet,
    ColorPalette,
    UITheme,
    WindowConfig,
)


def demo_theme_listing():
    """Show available themes."""
    print("=" * 60)
    print("AVAILABLE THEMES")
    print("=" * 60)
    for theme_name in ThemeManager.available_themes():
        print(f"  - {theme_name}")
    print()


def demo_get_configuration():
    """Show current configuration values."""
    print("=" * 60)
    print("CURRENT CONFIGURATION")
    print("=" * 60)
    
    theme = get_theme()
    colors = get_colors()
    fonts = get_fonts()
    window = get_window()
    
    print(f"Theme: {theme.name}")
    print(f"Debug mode: {theme.debug_mode}")
    print()
    
    print("Colors:")
    print(f"  Main background: {colors.main_bg}")
    print(f"  Text primary: {colors.text_primary}")
    print(f"  Accent orange: {colors.accent_orange}")
    print()
    
    print("Fonts:")
    print(f"  Family: {fonts.family}")
    print(f"  Base size: {fonts.size_base}px")
    print(f"  Title size: {fonts.size_title}px")
    print()
    
    print("Window:")
    print(f"  Size: {window.width}×{window.height}px")
    print(f"  Min size: {window.min_width}×{window.min_height}px")
    print(f"  Padding (large): {window.padding_lg}px")
    print(f"  Spacing (medium): {window.spacing_md}px")
    print()


def demo_switch_theme():
    """Show how to switch themes."""
    print("=" * 60)
    print("SWITCHING THEMES")
    print("=" * 60)
    
    original_theme = get_theme().name
    print(f"Original theme: {original_theme}")
    
    ThemeManager.set_theme("dev")
    print(f"Switched to: {get_theme().name}")
    print(f"New window size: {get_window().width}×{get_window().height}px")
    
    ThemeManager.set_theme(original_theme)
    print(f"Restored to: {get_theme().name}")
    print()


def demo_custom_theme():
    """Create and register a custom theme."""
    print("=" * 60)
    print("CREATING CUSTOM THEME")
    print("=" * 60)
    
    # Create a custom color palette
    custom_colors = ColorPalette(
        main_bg="#f5f0e8",
        card_bg="rgba(255, 250, 240, 0.95)",
        text_primary="#2a1800",
        accent_orange="#ff8c00",
    )
    
    # Create custom window config
    custom_window = WindowConfig(width=1024, height=768)
    
    # Combine into a theme
    custom_theme = UITheme(
        colors=custom_colors,
        fonts=get_fonts(),
        window=custom_window,
        name="my_theme",
        debug_mode=False,
    )
    
    # Register the theme
    ThemeManager.register_custom_theme("my_theme", custom_theme)
    print("Registered custom theme: my_theme")
    
    # Switch to it
    ThemeManager.set_theme("my_theme")
    print(f"Switched to custom theme")
    print(f"  Window size: {get_window().width}×{get_window().height}")
    print(f"  Main BG: {get_colors().main_bg}")
    print()


def demo_stylesheet_generation():
    """Show stylesheet generation."""
    print("=" * 60)
    print("STYLESHEET GENERATION")
    print("=" * 60)
    
    stylesheet = generate_stylesheet()
    lines = stylesheet.split("\n")
    print(f"Generated stylesheet with {len(lines)} lines")
    print("\nFirst 20 lines:")
    for line in lines[:20]:
        print(f"  {line}")
    print("  ...")
    print()


if __name__ == "__main__":
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "Configuration System Demo".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")
    print("\n")
    
    demo_theme_listing()
    demo_get_configuration()
    demo_switch_theme()
    demo_custom_theme()
    demo_stylesheet_generation()
    
    print("=" * 60)
    print("Demo complete!")
    print("=" * 60)
