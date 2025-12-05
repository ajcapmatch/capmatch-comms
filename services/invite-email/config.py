"""Configuration for invite-email service."""

import os
from typing import Optional
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parent
DEFAULT_INVITE_TEMPLATE_PATH = (
    APP_ROOT / "packages" / "email-templates" / "dist" / "invite-template.html"
)


class Config:
    """Environment-driven configuration."""

    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # Email / Resend
    RESEND_API_KEY: Optional[str] = os.getenv("RESEND_API_KEY")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "notifications@capmatch.com")
    RESEND_TEST_MODE: bool = os.getenv("RESEND_TEST_MODE", "true").lower() == "true"
    RESEND_TEST_RECIPIENT: Optional[str] = os.getenv("RESEND_TEST_RECIPIENT")
    RESEND_FORCE_TO_EMAIL: Optional[str] = os.getenv("RESEND_FORCE_TO_EMAIL")
    INVITE_EMAIL_DRY_RUN: bool = os.getenv("INVITE_EMAIL_DRY_RUN", "true").lower() == "true"

    # Template path
    INVITE_TEMPLATE_PATH: str = os.getenv(
        "INVITE_TEMPLATE_PATH",
        str(DEFAULT_INVITE_TEMPLATE_PATH),
    )

    # Polling configuration
    POLL_INTERVAL_SECONDS: int = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))

    # App base URL (for building accept-invite links)
    APP_BASE_URL: str = os.getenv("APP_BASE_URL")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> None:
        if not cls.SUPABASE_URL:
            raise ValueError("SUPABASE_URL environment variable is required")
        if not cls.SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable is required")
        if cls.POLL_INTERVAL_SECONDS < 1:
            raise ValueError("POLL_INTERVAL_SECONDS must be at least 1")
        if not cls.APP_BASE_URL:
            import logging
            logging.getLogger(__name__).warning(
                "APP_BASE_URL not set; accept-invite links will be incomplete"
            )



