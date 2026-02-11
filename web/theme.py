"""
Theme constants for PROSIM web interface.

Shared between app.py (middleware) and routes/theme.py (route).
"""

# Valid theme names (maps to CSS files: theme-{name}.css)
VALID_THEMES = ("win95", "industrial", "academic")
DEFAULT_THEME = "win95"
THEME_COOKIE_NAME = "prosim_theme"
