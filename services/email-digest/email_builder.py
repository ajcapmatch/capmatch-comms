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

def _template_candidates() -> list[Path]:
    """Return possible template locations, ordered by preference."""
    candidates: list[Path] = []

    configured_path = Path(Config.DIGEST_TEMPLATE_PATH).expanduser()
    if not configured_path.is_absolute():
        repo_root = Path(__file__).resolve().parents[2]
        configured_path = (repo_root / configured_path).resolve()
    candidates.append(configured_path)

    fallback_path = Path(__file__).parent / "templates" / "dist" / "digest-template.html"
    if fallback_path not in candidates:
        candidates.append(fallback_path)

    return candidates


def _load_template_html() -> tuple[str, Optional[Path]]:
    """Load the digest template HTML from the first available candidate path."""
    for candidate in _template_candidates():
        try:
            html = candidate.read_text(encoding="utf-8")
            logger.info("Loaded digest template from %s", candidate)
            return html, candidate
        except FileNotFoundError:
            logger.debug("Digest template not found at %s", candidate)
        except Exception:
            logger.exception("Failed reading digest template at %s", candidate)
    return "", None


TEMPLATE_HTML, TEMPLATE_PATH = _load_template_html()


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
    return '<span aria-hidden="true" style="font-size:18px;line-height:1;">✉️</span>'


def document_icon() -> str:
    return '<span aria-hidden="true" style="font-size:18px;line-height:1;">📄</span>'


def build_preview_text(events: List[Dict[str, Any]]) -> str:
    total_events = len(events)
    projects = {event["project_id"] for event in events}
    return f"{total_events} updates across {len(projects)} project(s)"

