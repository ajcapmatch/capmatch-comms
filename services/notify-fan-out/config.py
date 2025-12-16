"""Configuration for notify-fan-out service."""

import os


class Config:
    """Environment-driven configuration."""

    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # App base URL (for building notification links)
    APP_BASE_URL: str = os.getenv("APP_BASE_URL", "")

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if not cls.SUPABASE_URL:
            raise ValueError("SUPABASE_URL environment variable is required")
        if not cls.SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable is required")
