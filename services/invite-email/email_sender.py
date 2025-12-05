"""Resend-backed email sending for org invites."""

from __future__ import annotations

import logging
import time
from typing import Optional

from config import Config

try:
    import resend  # type: ignore[import-not-found]
    from resend import exceptions as resend_exceptions  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
    resend = None  # type: ignore
    resend_exceptions = None  # type: ignore


logger = logging.getLogger(__name__)

MAX_RETRIES = 3
REQUESTS_PER_SECOND = 2
THROTTLE_DELAY = 1 / REQUESTS_PER_SECOND


def _ensure_resend_api_key() -> None:
    if resend is None:
        raise ImportError(
            "The 'resend' package is not installed. Install dependencies via `uv sync`."
        )
    if not Config.RESEND_API_KEY:
        raise ValueError("RESEND_API_KEY is required to send emails via Resend.")
    if resend.api_key != Config.RESEND_API_KEY:
        resend.api_key = Config.RESEND_API_KEY


def _determine_recipient(user_email: str) -> str:
    """Return the email address Resend should target for this run."""
    if Config.RESEND_FORCE_TO_EMAIL:
        return Config.RESEND_FORCE_TO_EMAIL
    if Config.RESEND_TEST_MODE:
        if Config.RESEND_TEST_RECIPIENT:
            return Config.RESEND_TEST_RECIPIENT
        logger.warning(
            "RESEND_TEST_MODE is enabled but RESEND_TEST_RECIPIENT is unset; "
            "defaulting to the user's email (%s).",
            user_email,
        )
    return user_email


def send_invite_email(
    user_email: str,
    user_name: Optional[str],
    html_body: str,
    text_body: str,
    org_name: Optional[str],
) -> bool:
    """Send invite email (or log-only in dry-run mode)."""
    to_address = _determine_recipient(user_email)

    subject_org = f" to {org_name}" if org_name else ""
    subject = f"You're invited{subject_org} on CapMatch"

    logger.info("=" * 80)
    logger.info("ORG INVITE - Original recipient: %s", user_email)
    logger.info("ORG INVITE - Actual send-to: %s", to_address)
    logger.info("Subject: %s", subject)
    logger.info("-" * 80)
    logger.info("HTML Body:\n%s", html_body)
    logger.info("-" * 80)
    logger.info("Text Body:\n%s", text_body)
    logger.info("=" * 80)

    if Config.INVITE_EMAIL_DRY_RUN:
        logger.info(
            "INVITE_EMAIL_DRY_RUN=true -> not sending email to Resend; "
            "this is a log-only dry run."
        )
        return True

    try:
        _ensure_resend_api_key()
        accepted = _send_with_throttle_retry(
            {
                "from": Config.EMAIL_FROM,
                "to": [to_address],
                "subject": subject,
                "html": html_body,
                "text": text_body,
                "tags": [
                    {"name": "email_type", "value": "org_invite"},
                ],
            }
        )
        return accepted
    except resend_exceptions.ResendError as err:  # type: ignore[union-attr]
        logger.error("Resend API error sending to %s: %s", to_address, err)
        return False
    except Exception as exc:
        logger.exception("Unexpected error sending email to %s: %s", to_address, exc)
        return False


def _send_with_throttle_retry(params: dict) -> bool:
    """Call Resend with simple rate-limit handling."""
    for attempt in range(1, MAX_RETRIES + 1):
        if attempt > 1:
            sleep_for = THROTTLE_DELAY * attempt
            logger.info("Throttling before retry %d (sleep %.2fs)", attempt, sleep_for)
            time.sleep(sleep_for)
        else:
            time.sleep(THROTTLE_DELAY)

        try:
            response = resend.Emails.send(params)  # type: ignore[union-attr]
            message_id = response.get("id")
            logger.info("Resend send complete (id=%s)", message_id)
            return message_id is not None
        except resend_exceptions.RateLimitError as rate_err:  # type: ignore[union-attr]
            logger.warning(
                "Resend rate limit hit (attempt %d/%d): %s",
                attempt,
                MAX_RETRIES,
                rate_err,
            )
            if attempt == MAX_RETRIES:
                raise
        except resend_exceptions.ResendError:  # type: ignore[union-attr]
            raise
    return False


