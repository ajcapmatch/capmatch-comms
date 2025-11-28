"""Email template generation for digest emails."""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import Config

logger = logging.getLogger(__name__)

CTA_URL = "https://capmatch.com/dashboard"
MANAGE_PREFS_URL = "https://capmatch.com/settings/notifications"

TEMPLATE_PATH = Path(__file__).parent / "templates" / "dist" / "digest-template.html"
try:
    TEMPLATE_HTML = TEMPLATE_PATH.read_text(encoding="utf-8")
except FileNotFoundError:
    TEMPLATE_HTML = ""


def build_digest_email(
    events: List[Dict[str, Any]],
    user_name: Optional[str],
    project_names: Dict[str, str],
    user_id: str,
    digest_date: datetime,
) -> tuple[str, str]:
    if not events:
        return None, None

    if not TEMPLATE_HTML:
        logger.error("Digest template HTML not found at %s", TEMPLATE_PATH)
        return None, None

    by_project = defaultdict(lambda: defaultdict(list))
    for event in events:
        project_id = event["project_id"]
        event_type = event["event_type"]
        by_project[project_id][event_type].append(event)

    html_sections = []
    text_parts = [
        "CapMatch Daily Digest\n",
        f"Hey {user_name or 'there'}, here's what happened on {digest_date.strftime('%B %d, %Y')}\n\n",
    ]

    for project_id, event_types in by_project.items():
        project_name = project_names.get(project_id, "A project")
        html_sections.append(render_project_card(project_name, event_types, user_id))

        text_parts.append(f"{project_name}\n")
        text_parts.append("-" * len(project_name) + "\n")

        if "chat_message_sent" in event_types:
            messages = event_types["chat_message_sent"]
            count = len(messages)
            mentions = sum(
                1
                for msg in messages
                if user_id in msg.get("payload", {}).get("mentioned_user_ids", [])
            )
            mention_text = f" ({mentions} mentioned you)" if mentions else ""
            text_parts.append(f"- {count} new message(s){mention_text}\n")

        if "document_uploaded" in event_types:
            docs = event_types["document_uploaded"]
            count = len(docs)
            text_parts.append(f"- {count} new document upload(s)\n")

        text_parts.append("\n")

    html_body = (
        TEMPLATE_HTML.replace("{{PREVIEW_TEXT}}", build_preview_text(events))
        .replace("{{USER_NAME}}", user_name or "there")
        .replace("{{DIGEST_DATE}}", digest_date.strftime("%B %d, %Y"))
        .replace("{{CTA_URL}}", CTA_URL)
        .replace("{{MANAGE_PREFS_URL}}", MANAGE_PREFS_URL)
        .replace("<!--PROJECT_SECTIONS-->", "\n".join(html_sections))
    )

    text_parts.append(f"Open CapMatch: {CTA_URL}\n")
    text_parts.append(f"Manage preferences: {MANAGE_PREFS_URL}\n")

    return html_body, "".join(text_parts)


def render_project_card(project_name: str, event_types: dict, user_id: str) -> str:
    rows = []
    if "chat_message_sent" in event_types:
        messages = event_types["chat_message_sent"]
        count = len(messages)
        mentions = sum(
            1
            for msg in messages
            if user_id in msg.get("payload", {}).get("mentioned_user_ids", [])
        )
        mention_text = f" ({mentions} mentioned you)" if mentions else ""
        rows.append(
            f'<p style="display:flex;align-items:center;gap:10px;font-weight:500;color:#1F2937;margin:6px 0;"><span>{message_icon()}</span><span><strong>{count}</strong> new message(s){mention_text}</span></p>'
        )

    if "document_uploaded" in event_types:
        docs = event_types["document_uploaded"]
        count = len(docs)
        rows.append(
            f'<p style="display:flex;align-items:center;gap:10px;font-weight:500;color:#1F2937;margin:6px 0;"><span>{document_icon()}</span><span><strong>{count}</strong> new document upload(s)</span></p>'
        )

    if not rows:
        rows.append(
            '<p style="color:#94A3B8;font-size:14px;margin:6px 0;">No activity matched your preferences.</p>'
        )

    return (
        '<div style="background:#F8FAFF;border-radius:20px;border:1px solid #BFDBFE;padding:24px;margin-bottom:16px;">'
        f'<p style="font-size:18px;color:#3B82F6;margin:0 0 12px 0;font-weight:600;">{project_name}</p>'
        + "".join(rows)
        + "</div>"
    )


def message_icon() -> str:
    return '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h0a8.5 8.5 0 0 1 8.5 8.5Z"/></svg>'


def document_icon() -> str:
    return '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9Z"/><path d="M13 2v7h7"/><path d="M9 13h6"/><path d="M9 17h6"/></svg>'


def build_preview_text(events: List[Dict[str, Any]]) -> str:
    total_events = len(events)
    projects = {event["project_id"] for event in events}
    return f"{total_events} updates across {len(projects)} project(s)"

