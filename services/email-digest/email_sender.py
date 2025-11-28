"""Email sending functionality (Resend-backed)."""

from typing import Optional
import logging
import time

try:
    import resend  # type: ignore[import-not-found]
    from resend import exceptions as resend_exceptions  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
    resend = None  # type: ignore
    resend_exceptions = None  # type: ignore

MAX_RETRIES = 3

from config import Config

logger = logging.getLogger(__name__)

RESEND_REQUESTS_PER_SECOND = 2
RESEND_THROTTLE_DELAY = 1 / RESEND_REQUESTS_PER_SECOND


def _ensure_resend_api_key() -> None:
    """Populate resend.api_key before attempting to send."""
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


def send_digest_email(
    user_email: str,
    user_name: Optional[str],
    html_body: str,
    text_body: str,
    event_count: int
) -> bool:
    """
    Send digest email via Resend API.

    Returns True if sent successfully, False otherwise.
    """
    to_address = _determine_recipient(user_email)

    logger.info("=" * 80)
    logger.info("EMAIL DIGEST - Original recipient: %s", user_email)
    logger.info("EMAIL DIGEST - Actual send-to: %s", to_address)
    logger.info("Subject: Your CapMatch Daily Digest")
    logger.info("Events: %d", event_count)
    logger.info("-" * 80)
    logger.info("HTML Body:\n%s", html_body)
    logger.info("-" * 80)
    logger.info("Text Body:\n%s", text_body)
    logger.info("=" * 80)

    try:
        _ensure_resend_api_key()
        response = _send_with_throttle_retry(
            {
                "from": Config.EMAIL_FROM,
                "to": [to_address],
                "subject": "Your CapMatch Daily Digest",
                "html": html_body,
                "text": text_body,
                "tags": [
                    {"name": "event_count", "value": str(event_count)},
                ],
            }
        )
        return response
    except resend_exceptions.ResendError as err:
        logger.error("Resend API error sending to %s: %s", to_address, err)
        return False
    except Exception as exc:
        logger.exception("Unexpected error sending email to %s: %s", to_address, exc)
        return False


def _send_with_throttle_retry(params: dict) -> bool:
    """
    Call Resend with simple rate-limit handling.

    Resend's default free-tier limit is 2 requests/second. We delay before each attempt
    and retry once if we hit a 429 error.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        if attempt > 1:
            sleep_for = RESEND_THROTTLE_DELAY * attempt
            logger.info("Throttling before retry %d (sleep %.2fs)", attempt, sleep_for)
            time.sleep(sleep_for)
        else:
            time.sleep(RESEND_THROTTLE_DELAY)

        try:
            response = resend.Emails.send(params)
            message_id = response.get("id")
            logger.info("Resend send complete (id=%s)", message_id)
            return message_id is not None
        except resend_exceptions.RateLimitError as rate_err:
            logger.warning(
                "Resend rate limit hit (attempt %d/%d): %s",
                attempt,
                MAX_RETRIES,
                rate_err,
            )
            if attempt == MAX_RETRIES:
                raise
        except resend_exceptions.ResendError:
            raise
    return False
