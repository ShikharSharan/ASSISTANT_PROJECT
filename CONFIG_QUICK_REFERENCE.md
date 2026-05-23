# UI Configuration - Quick Reference

## Environment Setup

```bash
# Create .env file (see .env.example)
ASSISTANT_ENV=dev    # or 'prod'
GROQ_API_KEY=your_key
```

## Available Themes

| Theme | Window | Debug | Use Case |
|-------|--------|-------|----------|
| `prod` | 900×700 | ❌ | Production (default) |
| `dev` | 1000×800 | ✅ | Development & debugging |
| `high_contrast` | 900×700 | ❌ | Accessibility |

## Access Configuration

```python
# Import helpers
from app.ui_config import (
    ThemeManager,
    get_theme,
    get_colors,
    get_fonts,
    get_window,
)

# Get current values
window = get_window()
colors = get_colors()
fonts = get_fonts()

# Access specific properties
print(window.width)           # 900
print(colors.accent_orange)   # #ffd08a
print(fonts.size_base)        # 13
```

## Switch Themes

```python
from app.ui_config import ThemeManager

# Change theme at runtime
ThemeManager.set_theme('dev')
ThemeManager.set_theme('high_contrast')

# List available
ThemeManager.available_themes()
```

## Create Custom Theme

```python
from app.ui_config import (
    ThemeManager,
    UITheme,
    ColorPalette,
    FontConfig,
    WindowConfig,
)

# Define custom colors
colors = ColorPalette(
    main_bg="#1e1e1e",
    text_primary="#e0e0e0",
    accent_orange="#ff9500",
)

# Define custom window
window = WindowConfig(width=1200, height=900)

# Create theme
my_theme = UITheme(
    colors=colors,
    fonts=FontConfig(),
    window=window,
    name="my_custom_theme",
    debug_mode=False,
)

# Register and use
ThemeManager.register_custom_theme("my_custom_theme", my_theme)
ThemeManager.set_theme("my_custom_theme")
```

## Configuration Structure

```
app/ui_config.py
├── ColorPalette (50+ color properties)
├── FontConfig (font sizes)
├── WindowConfig (dimensions & spacing)
├── UITheme (bundle of above)
├── ThemeManager (registry & selection)
├── generate_stylesheet()
└── generate_combo_popup_stylesheet()

config.py
├── ENVIRONMENT ('dev' or 'prod')
└── Auto-initializes theme

app/ui.py
├── Uses get_window() for sizing
├── Uses generate_stylesheet() for styling
└── Uses generate_combo_popup_stylesheet() for popups
```

## Color Palette Reference

```python
colors = get_colors()

# Backgrounds
colors.main_bg              # #fff7ec
colors.card_bg              # rgba(255, 252, 246, 228)
colors.pending_bg           # rgba(255, 243, 224, 0.98)
colors.done_bg              # rgba(246, 242, 225, 0.98)
colors.focus_bg             # rgba(255, 249, 238, 0.98)

# Text
colors.text_primary         # #5a2800
colors.text_secondary       # #a9651d
colors.text_dark            # #7a3200

# Accents
colors.accent_orange        # #ffd08a
colors.accent_dark          # #e68700

# Status colors (High/Medium/Low priorities)
colors.priority_high        # #ffe0c1
colors.priority_medium      # #fff1d0
colors.priority_low         # #f5f0df
```

## Window Config Reference

```python
window = get_window()

# Dimensions
window.width                # 900
window.height               # 700
window.min_width            # 700
window.min_height           # 500

# Spacing & padding
window.padding_xl           # 20
window.padding_lg           # 16
window.padding_md           # 14
window.padding_sm           # 10
window.padding_xs           # 8

window.spacing_lg           # 12
window.spacing_md           # 10
window.spacing_sm           # 6

# Border radius
window.radius_lg            # 24
window.radius_md            # 18
window.radius_sm            # 14
window.radius_xs            # 10
```

## Font Config Reference

```python
fonts = get_fonts()

# Sizes
fonts.size_tiny             # 10
fonts.size_small            # 11
fonts.size_base             # 13
fonts.size_medium           # 14
fonts.size_large            # 15
fonts.size_xlarge           # 16
fonts.size_title            # 20
fonts.size_page_title       # 24

# Family
fonts.family                # "System"
```

## Dynamic Stylesheet

```python
from app.ui_config import generate_stylesheet, get_theme

# Generate stylesheet from current theme
stylesheet = generate_stylesheet()

# Generate from specific theme
specific_theme = ThemeManager._themes['dev']
stylesheet = generate_stylesheet(specific_theme)

# Set on widget
widget.setStyleSheet(stylesheet)
```

## Run Demo

```bash
python3 config_demo.py
```

Shows:
- Available themes
- Current configuration
- Theme switching
- Custom theme creation
- Stylesheet generation

## Common Tasks

### Change window size globally
```python
from app.ui_config import ThemeManager, UITheme, WindowConfig

window = WindowConfig(width=1400, height=900)
# Update current theme
current = ThemeManager.get_theme()
current.window = window
```

### Add new color to palette
```python
colors = ColorPalette()
colors.custom_color = "#deadbeef"
```

### Create dev-specific behavior
```python
from app.ui_config import get_theme

if get_theme().debug_mode:
    print("Debug mode enabled")
    # Add extra logging, UI elements, etc.
```

## Files to Know

- `config.py` - Environment config entry point
- `app/ui_config.py` - Theme definitions
- `app/ui.py` - Uses config system
- `CONFIGURATION.md` - Full documentation
- `.env.example` - Environment template
- `config_demo.py` - Runnable examples
