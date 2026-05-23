# Configuration Guide

## Environment Setup

The application supports **dev** and **prod** environment profiles, each with tailored UI settings.

### Setting the Environment

Create a `.env` file in the project root:

```bash
# Development environment (enhanced debugging, larger window)
ASSISTANT_ENV=dev

# Production environment (optimized, standard window size)
ASSISTANT_ENV=prod
```

If `ASSISTANT_ENV` is not set, the app defaults to `prod`.

## UI Configuration System

The new configuration system provides centralized management of:

- **Colors**: Primary backgrounds, text, accents, status indicators
- **Fonts**: Font sizes and families
- **Window**: Size, padding, spacing, border radius
- **Themes**: Pre-built themes for different use cases

### Available Themes

#### `prod` Theme (Default)
- Optimized for production use
- Standard window size: 900×700px
- Minimum size: 700×500px
- Default color palette (warm, cohesive)

#### `dev` Theme
- Enhanced for development and debugging
- Larger window size: 1000×800px
- Minimum size: 800×600px
- Same colors as prod for consistency
- `debug_mode=True` for future extensibility

#### `high_contrast` Theme
- Accessibility-focused alternative
- Darker text, modified accent colors
- Use: `ThemeManager.set_theme('high_contrast')`

### Programmatic Theme Selection

You can switch themes at runtime:

```python
from app.ui_config import ThemeManager

# Switch to dev theme
ThemeManager.set_theme('dev')

# Get current theme
current_theme = ThemeManager.get_theme()

# List available themes
available = ThemeManager.available_themes()
# Output: ['prod', 'dev', 'high_contrast']

# Register custom theme
from app.ui_config import UITheme, ColorPalette, FontConfig, WindowConfig

custom_palette = ColorPalette(main_bg="#f0f0f0", text_primary="#000000")
custom_theme = UITheme(
    colors=custom_palette,
    fonts=FontConfig(),
    window=WindowConfig(),
    name="custom",
    debug_mode=False
)
ThemeManager.register_custom_theme("custom", custom_theme)
ThemeManager.set_theme("custom")
```

### Accessing Configuration

```python
from app.ui_config import (
    get_theme,      # Get full UITheme
    get_colors,     # Get ColorPalette
    get_fonts,      # Get FontConfig
    get_window,     # Get WindowConfig
)

# Example: Access window dimensions
window_config = get_window()
print(window_config.width)      # 900
print(window_config.height)     # 700
print(window_config.padding_lg) # 16

# Example: Access colors
colors = get_colors()
print(colors.accent_orange)     # #ffd08a
print(colors.text_primary)      # #5a2800

# Example: Generate stylesheet dynamically
from app.ui_config import generate_stylesheet
stylesheet = generate_stylesheet()
widget.setStyleSheet(stylesheet)
```

## File Structure

- `config.py`: Main configuration entry point, handles environment detection
- `app/ui_config.py`: UI theme definitions and management
  - `ColorPalette`: Color definitions
  - `FontConfig`: Font settings
  - `WindowConfig`: Window and layout dimensions
  - `UITheme`: Complete theme bundle
  - `ThemeManager`: Theme registry and selection
  - `generate_stylesheet()`: Dynamic QSS generation
  - `generate_combo_popup_stylesheet()`: Combo popup styling

## Customization Examples

### Create a Dark Theme

```python
from app.ui_config import ThemeManager, UITheme, ColorPalette, FontConfig, WindowConfig

dark_palette = ColorPalette(
    main_bg="#1e1e1e",
    card_bg="rgba(40, 40, 40, 0.9)",
    text_primary="#e0e0e0",
    text_secondary="#b0b0b0",
    text_dark="#f0f0f0",
    accent_orange="#ff9500",
    accent_dark="#ff6600",
    # ... update other colors as needed
)

dark_theme = UITheme(
    colors=dark_palette,
    fonts=FontConfig(),
    window=WindowConfig(),
    name="dark",
    debug_mode=False
)

ThemeManager.register_custom_theme("dark", dark_theme)
ThemeManager.set_theme("dark")
```

### Adjust Window Size

```python
from app.ui_config import get_window

window = get_window()
# Now available:
# - window.width / height
# - window.min_width / min_height
# - window.padding_* (xl, lg, md, sm, xs)
# - window.spacing_* (lg, md, sm)
# - window.radius_* (lg, md, sm, xs)

# To modify, create a custom WindowConfig
custom_window = WindowConfig(
    width=1200,
    height=900,
    min_width=1000,
    min_height=700
)
```

## Migration from Hard-coded Values

Previously, UI settings were scattered across `ui.py`. Now they're centralized:

| Before | After |
|--------|-------|
| Hard-coded colors in stylesheet | `ColorPalette` dataclass |
| `self.resize(900, 600)` in `MainWindow.__init__` | `get_window().width / height` |
| String stylesheet concatenation | `generate_stylesheet()` function |
| No theme switching | `ThemeManager.set_theme()` |

The old `APP_STYLESHEET` constant still exists in `ui.py` for backward compatibility but is no longer used.

## Future Extensions

The configuration system is designed for easy extension:

1. **Settings persistence**: Save user preferences (theme, window size) to disk
2. **Runtime theme switching**: Add UI controls to change themes
3. **Theme marketplace**: Support loading themes from files
4. **Font customization**: Allow users to choose font sizes and families
5. **Color per-component**: Fine-tune individual component colors without regenerating entire stylesheet
