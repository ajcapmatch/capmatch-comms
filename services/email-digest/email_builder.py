"""Email template generation for digest emails."""

from typing import List, Dict, Any, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


def build_digest_email(
    events: List[Dict[str, Any]],
    user_name: Optional[str],
    project_names: Dict[str, str],
    user_id: str
) -> tuple[str, str]:
    """
    Build HTML and text versions of digest email.
    Groups events by project and event type.
    
    Returns: (html_body, text_body)
    """
    if not events:
        return None, None
    
    # Group events by project
    by_project = defaultdict(lambda: defaultdict(list))
    
    for event in events:
        project_id = event['project_id']
        event_type = event['event_type']
        by_project[project_id][event_type].append(event)
    
    # Build HTML
    html_parts = ["<h2>Your CapMatch Daily Digest</h2>"]
    html_parts.append(f"<p>Hi {user_name or 'there'},</p>")
    html_parts.append("<p>Here's what happened in your projects yesterday:</p>")
    html_parts.append("<hr>")
    
    # Build text
    text_parts = ["Your CapMatch Daily Digest\n\n"]
    text_parts.append(f"Hi {user_name or 'there'},\n\n")
    text_parts.append("Here's what happened in your projects yesterday:\n\n")
    text_parts.append("=" * 50 + "\n\n")
    
    # Render each project
    for project_id, event_types in by_project.items():
        project_name = project_names.get(project_id, "A project")
        html_parts.append(f"<h3>{project_name}</h3>")
        text_parts.append(f"{project_name}\n")
        text_parts.append("-" * len(project_name) + "\n")
        
        # Messages
        if 'chat_message_sent' in event_types:
            messages = event_types['chat_message_sent']
            count = len(messages)
            # Count mentions in messages for this project
            project_mentions = sum(
                1 for msg in messages
                if user_id in msg.get('payload', {}).get('mentioned_user_ids', [])
            )
            mention_text = f" ({project_mentions} mentioned you)" if project_mentions > 0 else ""
            html_parts.append(f"<p>💬 <strong>{count}</strong> new message{'s' if count > 1 else ''}{mention_text}</p>")
            text_parts.append(f"💬 {count} new message{'s' if count > 1 else ''}{mention_text}\n")
        
        # Document uploads
        if 'document_uploaded' in event_types:
            docs = event_types['document_uploaded']
            count = len(docs)
            html_parts.append(f"<p>📄 <strong>{count}</strong> new document{'s' if count > 1 else ''} uploaded</p>")
            text_parts.append(f"📄 {count} new document{'s' if count > 1 else ''} uploaded\n")
        
        html_parts.append("<br>")
        text_parts.append("\n")
    
    html_parts.append("<hr>")
    html_parts.append("<p><a href='https://capmatch.com/dashboard'>View in CapMatch →</a></p>")
    html_parts.append("<p style='color: #666; font-size: 12px;'>You're receiving this because you have email digest notifications enabled.</p>")
    
    text_parts.append("=" * 50 + "\n\n")
    text_parts.append("View in CapMatch: https://capmatch.com/dashboard\n\n")
    text_parts.append("You're receiving this because you have email digest notifications enabled.\n")
    
    html_body = "\n".join(html_parts)
    text_body = "\n".join(text_parts)
    
    return html_body, text_body

