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

    # Template path
    INVITE_TEMPLATE_PATH: str = os.getenv(
        "INVITE_TEMPLATE_PATH",
        str(DEFAULT_INVITE_TEMPLATE_PATH),
    )

    # Auth between Supabase edge function and this service
    INVITE_WEBHOOK_SECRET: str = os.getenv("INVITE_WEBHOOK_SECRET", "")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> None:
        if not cls.SUPABASE_URL:
            raise ValueError("SUPABASE_URL environment variable is required")
        if not cls.SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable is required")
        if not cls.RESEND_API_KEY:
            raise ValueError("RESEND_API_KEY environment variable is required")
        if not cls.INVITE_WEBHOOK_SECRET:
            raise ValueError("INVITE_WEBHOOK_SECRET environment variable is required")


