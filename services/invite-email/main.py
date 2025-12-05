"""Daemon service that polls for pending invites and sends emails."""

from __future__ import annotations

import logging
import signal
import sys
import time
from datetime import datetime
from typing import Any, Dict, Optional

from supabase import create_client, Client

from config import Config
from invite_email_builder import build_invite_email
from email_sender import send_invite_email

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Reduce noise from httpx and httpcore
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle SIGTERM/SIGINT for graceful shutdown."""
    global shutdown_requested
    logger.info("Received signal %d, shutting down gracefully...", signum)
    shutdown_requested = True


def get_supabase_client() -> Client:
    """Get Supabase client instance."""
    from supabase.client import ClientOptions

    return create_client(
        Config.SUPABASE_URL,
        Config.SUPABASE_SERVICE_ROLE_KEY,
        options=ClientOptions(
            postgrest_client_timeout=30,
            storage_client_timeout=30,
        ),
    )


def get_pending_invites(sb: Client) -> list[Dict[str, Any]]:
    """Fetch invites that need email sent."""
    response = (
        sb.table("invites")
        .select("id, status, email_sent_at, expires_at, token, org_id, invited_email, invited_by")
        .eq("status", "pending")
        .is_("email_sent_at", "null")
        .execute()
    )
    return response.data or []


def fetch_org_name(sb: Client, org_id: str) -> Optional[str]:
    """Fetch org name by ID."""
    try:
        response = (
            sb.table("orgs")
            .select("id, name")
            .eq("id", org_id)
            .maybe_single()
            .execute()
        )
        if response.data:
            return response.data.get("name")
    except Exception as e:
        logger.warning("Failed to fetch org name for %s: %s", org_id, e)
    return None


def fetch_inviter_name(sb: Client, inviter_id: str) -> Optional[str]:
    """Fetch inviter's full name by user ID."""
    try:
        response = (
            sb.table("profiles")
            .select("id, full_name")
            .eq("id", inviter_id)
            .maybe_single()
            .execute()
        )
        if response.data:
            return response.data.get("full_name")
    except Exception as e:
        logger.warning("Failed to fetch inviter name for %s: %s", inviter_id, e)
    return None


def parse_expires_at(expires_at_raw: Any) -> Optional[datetime]:
    """Parse expires_at from Supabase response."""
    if not expires_at_raw:
        return None
    if isinstance(expires_at_raw, str):
        try:
            # Supabase returns ISO8601 timestamps as strings
            return datetime.fromisoformat(expires_at_raw.replace("Z", "+00:00"))
        except Exception:
            logger.warning("Could not parse expires_at: %r", expires_at_raw)
            return None
    return expires_at_raw


def process_invite(sb: Client, invite: Dict[str, Any], app_base_url: str) -> bool:
    """
    Process a single invite: build and send email, then mark as sent.

    Returns True if successfully sent, False otherwise.
    """
    invite_id = invite["id"]
    logger.info("Processing invite %s for %s", invite_id, invite.get("invited_email"))

    # Fetch org and inviter display names
    org_id = invite.get("org_id")
    org_name = fetch_org_name(sb, org_id) if org_id else None

    inviter_id = invite.get("invited_by")
    inviter_name = fetch_inviter_name(sb, inviter_id) if inviter_id else None

    expires_at = parse_expires_at(invite.get("expires_at"))
    token = invite.get("token")

    if not token:
        logger.warning(
            "Invite %s has no token; still building email but link may not work",
            invite_id,
        )

    base_url = app_base_url.rstrip("/")
    accept_url = f"{base_url}/accept-invite?token={token}" if token else base_url

    # Build email
    html_body, text_body = build_invite_email(
        invited_email=invite["invited_email"],
        invitee_name=None,
        org_name=org_name,
        invited_by_name=inviter_name,
        accept_url=accept_url,
        expires_at=expires_at,
    )

    if not html_body or not text_body:
        logger.error("Failed to build invite email for invite %s", invite_id)
        return False

    # Send email
    success = send_invite_email(
        user_email=invite["invited_email"],
        user_name=None,
        html_body=html_body,
        text_body=text_body,
        org_name=org_name,
    )

    if not success:
        logger.error("Failed to send invite email for invite %s", invite_id)
        return False

    # Mark invite as emailed
    try:
        update_resp = (
            sb.table("invites")
            .update({"email_sent_at": "now()"})
            .eq("id", invite_id)
            .execute()
        )
        logger.info(
            "Invite %s emailed and marked sent (update=%s)",
            invite_id,
            update_resp.data,
        )
        return True
    except Exception as e:
        logger.error("Failed to update email_sent_at for invite %s: %s", invite_id, e)
        # Email was sent but DB update failed - this is a problem but we return True
        # since the email was actually delivered
        return True


def process_pending_invites(sb: Client, app_base_url: str) -> tuple[int, int]:
    """
    Process all pending invites.

    Returns (processed_count, failed_count).
    """
    invites = get_pending_invites(sb)
    if not invites:
        return 0, 0

    logger.info("Found %d pending invite(s) to process", len(invites))

    processed = 0
    failed = 0

    for invite in invites:
        if shutdown_requested:
            logger.info("Shutdown requested, stopping invite processing")
            break

        try:
            if process_invite(sb, invite, app_base_url):
                processed += 1
            else:
                failed += 1
        except Exception as e:
            logger.exception("Error processing invite %s: %s", invite.get("id"), e)
            failed += 1

    return processed, failed


def main():
    """Main daemon loop."""
    global shutdown_requested

    logger.info("=" * 80)
    logger.info("Starting CapMatch Invite Email Worker (daemon mode)")
    logger.info("=" * 80)

    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        logger.error("Configuration error: %s", e)
        sys.exit(1)

    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Get app base URL (for building accept links)
    app_base_url = Config.APP_BASE_URL or "http://localhost:3000"  # Default for local testing

    # Initialize Supabase client
    sb = get_supabase_client()
    logger.info("Connected to Supabase at %s", Config.SUPABASE_URL)

    poll_interval = Config.POLL_INTERVAL_SECONDS
    logger.info("Polling interval: %d seconds", poll_interval)
    logger.info("App base URL: %s", app_base_url)
    logger.info("=" * 80)

    total_processed = 0
    total_failed = 0
    cycle_count = 0

    try:
        while not shutdown_requested:
            cycle_count += 1
            cycle_start = time.time()

            logger.info("Poll cycle #%d: checking for pending invites...", cycle_count)

            try:
                processed, failed = process_pending_invites(sb, app_base_url)
                total_processed += processed
                total_failed += failed

                if processed > 0 or failed > 0:
                    logger.info(
                        "Cycle #%d: processed %d, failed %d (total: %d processed, %d failed)",
                        cycle_count,
                        processed,
                        failed,
                        total_processed,
                        total_failed,
                    )
            except Exception as e:
                logger.exception("Error in poll cycle #%d: %s", cycle_count, e)

            if shutdown_requested:
                break

            # Sleep until next poll, but check shutdown flag periodically
            sleep_remaining = poll_interval
            while sleep_remaining > 0 and not shutdown_requested:
                sleep_chunk = min(5.0, sleep_remaining)  # Check every 5 seconds
                time.sleep(sleep_chunk)
                sleep_remaining -= sleep_chunk

            cycle_duration = time.time() - cycle_start
            if cycle_duration > poll_interval:
                logger.warning(
                    "Poll cycle #%d took %.2fs (longer than interval %ds)",
                    cycle_count,
                    cycle_duration,
                    poll_interval,
                )

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        shutdown_requested = True

    logger.info("=" * 80)
    logger.info("Shutting down invite email worker")
    logger.info("Total cycles: %d", cycle_count)
    logger.info("Total invites processed: %d", total_processed)
    logger.info("Total invites failed: %d", total_failed)
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
