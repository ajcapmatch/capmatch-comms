"""Build HTML and text bodies for org invite emails."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import Config

logger = logging.getLogger(__name__)


def _load_template_html() -> tuple[str, Optional[Path]]:
    """Load the invite template HTML from configured path."""
    configured = Path(Config.INVITE_TEMPLATE_PATH).expanduser()
    if not configured.is_absolute():
        app_root = Path(__file__).resolve().parent
        configured = (app_root / configured).resolve()

    try:
        html = configured.read_text(encoding="utf-8")
        logger.info("Loaded invite template from %s", configured)
        return html, configured
    except FileNotFoundError:
        logger.error("Invite template HTML not found at %s", configured)
    except Exception:
        logger.exception("Failed reading invite template at %s", configured)
    return "", None


TEMPLATE_HTML, TEMPLATE_PATH = _load_template_html()


def build_invite_email(
    *,
    invited_email: str,
    invitee_name: Optional[str],
    org_name: Optional[str],
    invited_by_name: Optional[str],
    accept_url: str,
    expires_at: Optional[datetime],
) -> tuple[Optional[str], Optional[str]]:
    """
    Build invite email bodies.

    Returns (html_body, text_body) or (None, None) if template is unavailable.
    """
    if not TEMPLATE_HTML:
        logger.error("Invite template HTML not available; cannot build email.")
        return None, None

    display_invitee = invitee_name or invited_email
    display_org = org_name or "CapMatch"
    inviter = invited_by_name or "a member of your team"
    expires_text = (
        expires_at.strftime("%B %d, %Y")
        if expires_at is not None
        else "soon"
    )

    html_body = (
        TEMPLATE_HTML.replace("{{INVITEE_NAME}}", display_invitee)
        .replace("{{ORG_NAME}}", display_org)
        .replace("{{INVITED_BY_NAME}}", inviter)
        .replace("{{ACCEPT_URL}}", accept_url)
        .replace("{{EXPIRES_TEXT}}", expires_text)
    )

    text_lines = [
        f"Hi {display_invitee},",
        "",
        f"You've been invited to join {display_org} on CapMatch by {inviter}.",
        "",
        f"Open this link to accept your invite: {accept_url}",
        "",
        f"This invite will expire on {expires_text}.",
        "",
        "If you weren't expecting this, you can ignore this email.",
    ]

    return html_body, "\n".join(text_lines)


