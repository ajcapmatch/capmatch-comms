"""Configuration for notify-fan-out service."""

import os
from typing import Optional


class Config:
    """Environment-driven configuration."""

    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # Server
    PORT: int = int(os.getenv("PORT", "8080"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    # Webhook authentication (optional shared secret)
    # If set, incoming requests must send:
    #   Authorization: Bearer <WEBHOOK_SECRET>
    WEBHOOK_SECRET: Optional[str] = os.getenv("WEBHOOK_SECRET")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # App base URL (if you ever need it for links)
    APP_BASE_URL: str = os.getenv("APP_BASE_URL", "")

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if not cls.SUPABASE_URL:
            raise ValueError("SUPABASE_URL environment variable is required")
        if not cls.SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable is required")


