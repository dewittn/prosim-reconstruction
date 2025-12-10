"""
Web application configuration for PROSIM.

Loads settings from environment variables with sensible defaults.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class WebConfig:
    """Configuration for the PROSIM web application."""

    # Application settings
    app_name: str = "PROSIM"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database settings
    database_url: str = "sqlite:///./data/prosim.db"

    # Session settings
    secret_key: str = "dev-secret-key-change-in-production"
    session_cookie_name: str = "prosim_session"
    session_max_age: int = 60 * 60 * 24 * 365  # 1 year

    # Server settings
    host: str = "127.0.0.1"
    port: int = 8000

    # Paths (set in __post_init__)
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent)
    templates_dir: Optional[Path] = None
    static_dir: Optional[Path] = None
    data_dir: Optional[Path] = None

    def __post_init__(self) -> None:
        """Set derived paths after initialization."""
        if self.templates_dir is None:
            self.templates_dir = self.base_dir / "templates"
        if self.static_dir is None:
            self.static_dir = self.base_dir / "static"
        if self.data_dir is None:
            self.data_dir = self.base_dir.parent / "data"

    @classmethod
    def from_env(cls) -> "WebConfig":
        """Create config from environment variables."""
        return cls(
            debug=os.getenv("PROSIM_DEBUG", "").lower() in ("true", "1", "yes"),
            database_url=os.getenv("PROSIM_DATABASE_URL", "sqlite:///./data/prosim.db"),
            secret_key=os.getenv(
                "PROSIM_SECRET_KEY", "dev-secret-key-change-in-production"
            ),
            host=os.getenv("PROSIM_HOST", "127.0.0.1"),
            port=int(os.getenv("PROSIM_PORT", "8000")),
        )

    def ensure_data_dir(self) -> Path:
        """Ensure the data directory exists and return its path."""
        assert self.data_dir is not None, "data_dir must be set"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir


def get_config() -> WebConfig:
    """Get the web configuration instance."""
    return WebConfig.from_env()


# Global config instance (lazy initialization)
_config: Optional[WebConfig] = None


def get_settings() -> WebConfig:
    """Get or create the global config instance."""
    global _config
    if _config is None:
        _config = get_config()
    return _config
