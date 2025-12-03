"""FastAPI service that sends org invite emails."""

from __future__ import annotations

import hmac
import logging
import os
import time
from hashlib import sha256
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from supabase import create_client

from config import Config
from invite_email_builder import build_invite_email
from email_sender import send_invite_email


logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="CapMatch Invite Email Service")


class SendInvitePayload(BaseModel):
    invite_id: str
    invited_email: str
    org_id: str
    role: str
    invited_by_user_id: str
    app_base_url: str


def _verify_signature(
    *,
    secret: str,
    timestamp: str,
    body: bytes,
    provided_signature: str,
) -> None:
    if not secret:
        logger.error("INVITE_WEBHOOK_SECRET is not configured.")
        raise HTTPException(status_code=500, detail="Invite webhook misconfigured")

    try:
        ts = int(timestamp)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timestamp")

    now = int(time.time())
    # 5 minute window
    if abs(now - ts) > 300:
        raise HTTPException(status_code=400, detail="Stale timestamp")

    payload = f"{timestamp}.".encode("utf-8") + body
    expected = hmac.new(secret.encode("utf-8"), payload, sha256).hexdigest()

    if not hmac.compare_digest(expected, provided_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")


def _get_supabase_client():
    return create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_ROLE_KEY)


@app.post("/send-invite")
async def send_invite(
    payload: SendInvitePayload,
    x_capmatch_timestamp: str = Header(..., alias="X-Capmatch-Timestamp"),
    x_capmatch_invite_signature: str = Header(..., alias="X-Capmatch-Invite-Signature"),
) -> Dict[str, Any]:
    """
    Send an org invite email.

    This endpoint is expected to be called from a Supabase edge function with
    an HMAC-signed payload. It is safe to call multiple times; if the invite
    has already been emailed or is no longer pending, it will no-op.
    """
    raw_body = payload.model_dump_json().encode("utf-8")
    _verify_signature(
        secret=Config.INVITE_WEBHOOK_SECRET,
        timestamp=x_capmatch_timestamp,
        body=raw_body,
        provided_signature=x_capmatch_invite_signature,
    )

    Config.validate()
    sb = _get_supabase_client()

    # Fetch invite row and related display info
    invite_resp = (
        sb.table("invites")
        .select("id, status, email_sent_at, expires_at, token, org_id, invited_email, invited_by")
        .eq("id", payload.invite_id)
        .maybe_single()
        .execute()
    )
    invite = invite_resp.data
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")

    if invite.get("status") != "pending":
        logger.info(
            "[invite-email] invite %s is not pending (status=%s); skipping",
            invite["id"],
            invite.get("status"),
        )
        return {
            "status": "not_pending",
            "invite_id": invite["id"],
        }

    if invite.get("email_sent_at"):
        logger.info("[invite-email] invite %s already emailed; skipping", invite["id"])
        return {
            "status": "already_sent",
            "invite_id": invite["id"],
            "email_sent_at": invite["email_sent_at"],
        }

    # Fetch org and inviter display names
    org_name: Optional[str] = None
    inviter_name: Optional[str] = None

    org_id = invite.get("org_id") or payload.org_id
    if org_id:
        org_resp = (
            sb.table("orgs")
            .select("id, name")
            .eq("id", org_id)
            .maybe_single()
            .execute()
        )
        if org_resp.data:
            org_name = org_resp.data.get("name")

    inviter_id = invite.get("invited_by") or payload.invited_by_user_id
    if inviter_id:
        inviter_resp = (
            sb.table("profiles")
            .select("id, full_name")
            .eq("id", inviter_id)
            .maybe_single()
            .execute()
        )
        if inviter_resp.data:
            inviter_name = inviter_resp.data.get("full_name")

    expires_at_raw = invite.get("expires_at")
    expires_at_dt: Optional[datetime] = None
    if isinstance(expires_at_raw, str):
        try:
            # Supabase returns ISO8601 timestamps as strings
            from datetime import datetime

            expires_at_dt = datetime.fromisoformat(expires_at_raw.replace("Z", "+00:00"))
        except Exception:
            logger.warning(
                "[invite-email] could not parse expires_at for invite %s: %r",
                invite["id"],
                expires_at_raw,
            )
    else:
        expires_at_dt = expires_at_raw

    token = invite.get("token")
    if not token:
        logger.warning(
            "[invite-email] invite %s has no token; still building email but link may not work",
            invite["id"],
        )

    base_url = payload.app_base_url.rstrip("/")
    accept_url = f"{base_url}/accept-invite?token={token}" if token else base_url

    html_body, text_body = build_invite_email(
        invited_email=invite["invited_email"],
        invitee_name=None,
        org_name=org_name,
        invited_by_name=inviter_name,
        accept_url=accept_url,
        expires_at=expires_at_dt,
    )

    if not html_body or not text_body:
        raise HTTPException(status_code=500, detail="Failed to build invite email body")

    success = send_invite_email(
        user_email=invite["invited_email"],
        user_name=None,
        html_body=html_body,
        text_body=text_body,
        org_name=org_name,
    )

    if not success:
        raise HTTPException(status_code=502, detail="Failed to send invite email")

    # Mark invite as emailed
    update_resp = (
        sb.table("invites")
        .update({"email_sent_at": "now()"})
        .eq("id", invite["id"])
        .execute()
    )
    logger.info(
        "[invite-email] invite %s emailed and marked sent (update=%s)",
        invite["id"],
        update_resp.data,
    )

    return {
        "status": "sent",
        "invite_id": invite["id"],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )


