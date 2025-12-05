"""Build HTML and text bodies for org invite emails."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import Config

logger = logging.getLogger(__name__)


def _template_candidates() -> list[Path]:
    """Return possible template locations, ordered by preference."""
    candidates: list[Path] = []

    configured_path = Path(Config.INVITE_TEMPLATE_PATH).expanduser()
    if not configured_path.is_absolute():
        # Interpret relative paths as relative to the application root (/app),
        # where this module lives in the Docker image.
        app_root = Path(__file__).resolve().parent
        configured_path = (app_root / configured_path).resolve()
    candidates.append(configured_path)

    # Fallback: legacy location (for backwards compatibility)
    fallback_path = Path(__file__).parent / "templates" / "dist" / "invite-template.html"
    if fallback_path not in candidates:
        candidates.append(fallback_path)

    return candidates


def _load_template_html() -> tuple[str, Optional[Path]]:
    """Load the invite template HTML from the first available candidate path."""
    for candidate in _template_candidates():
        try:
            html = candidate.read_text(encoding="utf-8")
            logger.info("Loaded invite template from %s", candidate)
            return html, candidate
        except FileNotFoundError:
            logger.debug("Invite template not found at %s", candidate)
        except Exception:
            logger.exception("Failed reading invite template at %s", candidate)
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

    Returns (html_body, text_body). If template is unavailable, generates simple HTML/text.
    """
    display_invitee = invitee_name or invited_email
    display_org = org_name or "CapMatch"
    inviter = invited_by_name or "a member of your team"
    expires_text = (
        expires_at.strftime("%B %d, %Y")
        if expires_at is not None
        else "soon"
    )

    # Build text body (always available)
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
    text_body = "\n".join(text_lines)

    # Build HTML body
    if not TEMPLATE_HTML:
        logger.error("Invite template HTML not available; cannot build email.")
        return None, None

    html_body = (
        TEMPLATE_HTML.replace("{{INVITEE_NAME}}", display_invitee)
        .replace("{{ORG_NAME}}", display_org)
        .replace("{{INVITED_BY_NAME}}", inviter)
        .replace("{{ACCEPT_URL}}", accept_url)
        .replace("{{EXPIRES_TEXT}}", expires_text)
    )

    return html_body, text_body


