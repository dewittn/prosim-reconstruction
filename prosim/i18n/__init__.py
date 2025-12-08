"""
Internationalization support for PROSIM.

This module provides multilingual support using JSON locale files.
"""

import json
from pathlib import Path
from typing import Any

_LOCALES_DIR = Path(__file__).parent / "locales"
_current_locale: dict[str, Any] = {}
_current_language: str = "en"


def load_locale(language: str = "en") -> dict[str, Any]:
    """
    Load a locale file for the specified language.

    Args:
        language: Language code (e.g., 'en', 'es')

    Returns:
        Dictionary of translated strings
    """
    global _current_locale, _current_language

    locale_file = _LOCALES_DIR / f"{language}.json"
    if not locale_file.exists():
        # Fall back to English
        locale_file = _LOCALES_DIR / "en.json"
        language = "en"

    if locale_file.exists():
        with open(locale_file, "r", encoding="utf-8") as f:
            _current_locale = json.load(f)
    else:
        _current_locale = {}

    _current_language = language
    return _current_locale


def t(key: str, **kwargs: Any) -> str:
    """
    Translate a key to the current locale.

    Args:
        key: Translation key (dot-separated path, e.g., 'menu.new_game')
        **kwargs: Format arguments for string interpolation

    Returns:
        Translated string, or the key itself if not found
    """
    if not _current_locale:
        load_locale()

    # Navigate nested keys
    parts = key.split(".")
    value: Any = _current_locale
    for part in parts:
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return key  # Key not found, return as-is

    if isinstance(value, str):
        try:
            return value.format(**kwargs)
        except KeyError:
            return value

    return key


def get_available_languages() -> list[str]:
    """Return list of available language codes."""
    return [f.stem for f in _LOCALES_DIR.glob("*.json")]


def get_current_language() -> str:
    """Return the current language code."""
    return _current_language
