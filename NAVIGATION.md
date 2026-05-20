# Navigation System

## Overview

The application now features a **persistent left sidebar** for global navigation, replacing the scattered navigation buttons throughout individual pages.

### Key Features

✅ **Persistent sidebar** - Always visible, provides quick access to main sections  
✅ **Visual active state** - Current page is highlighted with orange background  
✅ **Emoji icons** - Quick visual identification of sections  
✅ **Smooth navigation** - Pages refresh context when navigated to  
✅ **Responsive layout** - Fixed-width sidebar (180px) + flexible content area

## Navigation Structure

### Sidebar Sections

The sidebar provides one-click access to four main sections:

| Icon | Section | ID | Purpose |
|------|---------|-----|---------|
| 🏠 | Home | `home` | Dashboard with focus task, AI nudge, quick stats |
| ✓ | Tasks | `tasks` | Full task management (add, edit, filter, complete) |
| 💰 | Money | `money` | Financial tracking (income, expenses, EMI, loans) |
| ✨ | Assistant | `ai` | AI chat with contextual suggestions |

### Page Hierarchy

```
Dashboard (Home)
├── Task Management (Tasks)
│   ├── Add Task (modal form)
│   └── Task Details (modal form)
├── Financial Tracking (Money)
└── AI Assistant Chat (AI)
```

Modal pages (Add Task, Task Details) maintain their own navigation since they're context-specific.

## Implementation

### Components

#### NavigationBar Class
Located in `app/ui.py`, handles:
- Sidebar rendering
- Button creation and styling
- Active state management
- Navigation callbacks

```python
class NavigationBar(QFrame):
    """Persistent navigation sidebar with main application sections."""
    
    def __init__(self, main_window):
        # Creates sidebar with nav buttons
        # Manages active state based on current page
    
    def _navigate(self, nav_id: str):
        # Handles button clicks
        # Routes to appropriate page
    
    def set_active_page(self, page_type: str):
        # Updates active button styling
```

#### MainWindow Layout
MainWindow now uses horizontal layout:
- **Left**: NavigationBar (fixed width 180px)
- **Right**: QStackedWidget with pages

```python
central_widget = QWidget()
central_layout = QHBoxLayout()
central_layout.addWidget(self.nav_bar)      # Sidebar
central_layout.addWidget(self.stack)        # Content
self.setCentralWidget(central_widget)
```

### Styling

Navigation styles defined in `app/ui_config.py` `generate_stylesheet()`:

```qss
QWidget#navigationBar {
    background-color: #faf3e6;
    border-right: 1px solid rgba(227, 166, 66, 0.28);
}

QPushButton#navButton {
    background-color: transparent;
    color: #5a2800;
    border: none;
    border-radius: 8px;
    padding: 8px 12px;
    margin: 0 8px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton#navButton[active="true"] {
    background-color: #ffd08a;    /* Orange highlight */
    color: #6b2a00;
    font-weight: 700;
}
```

## Usage

### Navigate Programmatically

```python
# From any page or component
self.main_window.show_home_page()
self.main_window.show_tasks_page()
self.main_window.show_money_page()
self.main_window.show_ai_chat_page()
```

### Update Active State

The navigation bar automatically updates when pages are shown. Each `show_*_page()` method calls:

```python
self.nav_bar.set_active_page("home")  # or "tasks", "money", "ai"
```

### Add New Navigation Item

To add a new main section:

1. Create the new page class (e.g., `class SettingsPage(InfinityPage)`)
2. Add to MainWindow:
   ```python
   self.settings_page = SettingsPage(self, ...)
   self.stack.addWidget(self.settings_page)
   ```
3. Add navigation button in NavigationBar:
   ```python
   self.nav_items["settings"] = self._create_nav_button("⚙ Settings", "settings")
   ```
4. Add handler in NavigationBar._navigate():
   ```python
   elif nav_id == "settings":
       self.main_window.show_settings_page()
   ```
5. Add show_settings_page() in MainWindow:
   ```python
   def show_settings_page(self):
       self.stack.setCurrentWidget(self.settings_page)
       self.nav_bar.set_active_page("settings")
   ```

## Design Decisions

### Why Sidebar vs Tab Bar?

- **Sidebar**: More extensible, can accommodate more items, cleaner spacing
- **Tab Bar**: Horizontal space limited in typical window widths
- **Current choice**: Sidebar (180px fixed width) provides better UX for 4+ items

### Why Fixed Width?

- Consistent layout regardless of content
- Easier touch targeting on buttons
- Prevents layout shifts when switching pages
- Better for dark mode / theme switching

### Why Auto-Active State?

- Every page navigation updates the sidebar
- Prevents stale active states
- Provides visual feedback of current location
- Reduces complexity of manual state management

## Related Files

| File | Purpose |
|------|---------|
| `app/ui.py` | NavigationBar class & MainWindow layout |
| `app/ui_config.py` | Navigation styling in generate_stylesheet() |
| [NAVIGATION.md](NAVIGATION.md) | This file |

## Future Enhancements

### Planned Features

1. **Sidebar collapse/expand** - Hamburger menu to hide labels
2. **Navigation history** - Back/forward buttons
3. **Page indicators** - Badge count for pending tasks, unread messages
4. **Custom themes** - Different navigation colors per theme
5. **Keyboard shortcuts** - Alt+H for Home, Alt+T for Tasks, etc.
6. **Recent pages** - Quick access to frequently visited pages

### Possible Improvements

- Add icons (not just emojis) for better visual appeal
- Tooltip on hover showing full page name
- Breadcrumb navigation for nested pages
- Animation on active state change
- Responsive width (hide labels on small screens)

## Troubleshooting

### Navigation buttons not responding
- Check NavigationBar is properly initialized in MainWindow
- Verify page exists before navigation
- Check console for import errors

### Active state not updating
- Ensure show_*_page() calls nav_bar.set_active_page()
- Check that page_type string matches nav_items keys
- Verify repolish(btn) is called after setProperty

### Sidebar not visible
- Check NavigationBar is added to central_layout
- Verify setFixedWidth(180) is set
- Check stylesheet isn't hiding it (background: transparent)

## Code Examples

### Example: Navigate from Page Code

```python
class HomePage(InfinityPage):
    def __init__(self, main_window, ...):
        self.main_window = main_window
    
    def go_to_tasks(self):
        self.main_window.show_tasks_page()
```

### Example: Custom Navigation Handler

```python
class NavigationBar(QFrame):
    def _navigate(self, nav_id: str):
        handlers = {
            "home": self.main_window.show_home_page,
            "tasks": self.main_window.show_tasks_page,
            "money": self.main_window.show_money_page,
            "ai": self.main_window.show_ai_chat_page,
        }
        if nav_id in handlers:
            handlers[nav_id]()
        self._set_active(nav_id)
```

### Example: Add Badge Count

```python
# In NavigationBar
self.nav_items["tasks"] = self._create_nav_button("✓ Tasks (5)", "tasks")

# Update after data changes
def update_task_count(self, count: int):
    self.nav_items["tasks"].setText(f"✓ Tasks ({count})")
```
