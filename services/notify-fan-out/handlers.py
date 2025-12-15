"""Event handlers for notify-fan-out service."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from database import Database, DomainEvent

logger = logging.getLogger(__name__)


@dataclass
class HandlerResult:
    """Result of handling an event."""

    inserted: int = 0
    updated: int = 0
    skipped: bool = False
    reason: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"inserted": self.inserted}
        if self.updated:
            result["updated"] = self.updated
        if self.skipped:
            result["skipped"] = self.skipped
        if self.reason:
            result["reason"] = self.reason
        if self.error:
            result["error"] = self.error
        return result


def handle_document_upload(db: Database, event: DomainEvent) -> HandlerResult:
    """Handle document_uploaded event."""
    logger.info("Processing document_uploaded event: %d", event.id)

    # Collect candidate user IDs
    candidate_ids = db.collect_candidate_user_ids(event)
    if not candidate_ids:
        return HandlerResult(inserted=0, reason="no_candidates")

    # Filter by resource access
    filtered_user_ids = db.filter_by_resource_access(candidate_ids, event.resource_id)

    # Exclude actor
    final_recipient_ids = [uid for uid in filtered_user_ids if uid and uid != event.actor_id]

    if not final_recipient_ids:
        return HandlerResult(inserted=0, reason="no_authorized_recipients")

    # Filter by preferences
    notified_ids: List[str] = []
    for user_id in final_recipient_ids:
        is_muted = db.check_user_preference_muted(
            user_id=user_id,
            scope_type="project",
            scope_id=event.project_id,
            event_type="document_uploaded",
            channel="in_app",
            project_id=event.project_id,
        )
        if not is_muted:
            notified_ids.append(user_id)

    if not notified_ids:
        return HandlerResult(inserted=0, reason="all_muted")

    # Check for duplicates
    already_notified = db.get_existing_notification_recipients(event.id)
    recipients_to_insert = [uid for uid in notified_ids if uid not in already_notified]

    if not recipients_to_insert:
        return HandlerResult(inserted=0, reason="already_notified")

    # Build notification payload
    file_name = event.payload.get("fileName", "A new file")
    project_name = db.get_project_name(event.project_id)
    base_path = f"/project/workspace/{event.project_id}"
    link_url = f"{base_path}?resourceId={event.resource_id}" if event.resource_id else base_path

    rows = [
        {
            "user_id": user_id,
            "event_id": event.id,
            "title": f"Document uploaded - {project_name}",
            "body": f'New file **"{file_name}"** was uploaded to **{project_name}**.',
            "link_url": link_url,
        }
        for user_id in recipients_to_insert
    ]

    inserted = db.insert_notifications_batch(rows)
    return HandlerResult(inserted=inserted)


def handle_chat_message(db: Database, event: DomainEvent) -> HandlerResult:
    """Handle chat_message_sent event."""
    logger.info("Processing chat_message_sent event: %d", event.id)

    if not event.thread_id:
        return HandlerResult(error="Missing thread_id for chat event")

    # Get thread info
    thread_info = db.get_thread_info(event.thread_id)
    thread_name = (thread_info.get("topic") or "thread").strip() if thread_info else "thread"
    thread_label = thread_name if thread_name.startswith("#") else f"#{thread_name}"
    project_id = thread_info.get("project_id") if thread_info else event.project_id
    project_name = db.get_project_name(project_id)
    thread_descriptor = thread_label
    project_descriptor = project_name or "this project"

    # Get participants
    participants = db.get_thread_participants(event.thread_id)

    # Get sender name
    sender_name = db.get_profile_name(event.actor_id)

    mentioned_user_ids = event.payload.get("mentioned_user_ids") or []
    full_content = event.payload.get("full_content") or "New message"

    thread_payload_base = {
        "count": 1,
        "thread_id": event.thread_id,
        "thread_name": thread_name,
        "project_name": project_name,
        "type": "thread_activity",
    }

    inserted_count = 0
    updated_count = 0

    for participant in participants:
        user_id = participant.get("user_id")
        if not user_id or user_id == event.actor_id:
            continue

        # Check preferences
        is_muted = db.check_user_preference_muted(
            user_id=user_id,
            scope_type="thread",
            scope_id=event.thread_id,
            event_type="chat_message",
            channel="in_app",
            project_id=project_id,
        )

        if is_muted:
            continue

        # Generate link URL
        base_path = f"/project/workspace/{project_id}"
        link_url = f"{base_path}?tab=chat&thread={event.thread_id}"

        # Determine notification type
        is_mentioned = user_id in mentioned_user_ids

        if is_mentioned:
            # MENTIONS: Always create new notification
            if db.insert_notification(
                user_id=user_id,
                event_id=event.id,
                title=f"{sender_name} mentioned you in {thread_label} - {project_name}",
                body=full_content,
                link_url=link_url,
                payload={**thread_payload_base, "type": "mention"},
            ):
                inserted_count += 1
        else:
            # GENERAL: Aggregate if possible
            existing_notif = db.get_unread_thread_notification(user_id, event.thread_id)

            if existing_notif and existing_notif.get("id"):
                if db.increment_notification_count(existing_notif["id"]):
                    updated_count += 1
            else:
                if db.insert_notification(
                    user_id=user_id,
                    event_id=event.id,
                    title=f"New messages in {project_descriptor}",
                    body=f"1 new message in **{thread_descriptor}**",
                    link_url=link_url,
                    payload=thread_payload_base,
                ):
                    inserted_count += 1

    return HandlerResult(inserted=inserted_count, updated=updated_count)


def handle_meeting_invitation(db: Database, event: DomainEvent) -> HandlerResult:
    """Handle meeting_invited event."""
    logger.info(
        "Processing meeting_invited event: %d, meeting_id: %s",
        event.id,
        event.meeting_id,
    )

    invited_user_id = event.payload.get("invited_user_id")

    if not invited_user_id or not event.meeting_id:
        logger.error(
            "Missing invited_user_id or meeting_id: invited=%s, meeting=%s",
            invited_user_id,
            event.meeting_id,
        )
        return HandlerResult(inserted=0, reason="missing_required_data")

    # Check for existing notification
    already_notified = db.get_existing_notification_recipients(event.id)
    if invited_user_id in already_notified:
        return HandlerResult(inserted=0, reason="already_notified")

    # Check user preferences
    scope_type = "project" if event.project_id else "global"
    is_muted = db.check_user_preference_muted(
        user_id=invited_user_id,
        scope_type=scope_type,
        scope_id=event.project_id or "",
        event_type="meeting_invited",
        channel="in_app",
        project_id=event.project_id or "",
    )

    if is_muted:
        return HandlerResult(inserted=0, reason="user_muted")

    # Get organizer name
    organizer_name = db.get_profile_name(event.actor_id)

    # Extract meeting details
    meeting_title = event.payload.get("meeting_title") or "a meeting"
    start_time = event.payload.get("start_time")

    # Get project name
    project_name = db.get_project_name(event.project_id) if event.project_id else None

    # Build notification
    title = (
        f"{organizer_name} invited you to a meeting - {project_name}"
        if project_name
        else f"{organizer_name} invited you to a meeting"
    )

    body = f"**{meeting_title}**"
    if start_time:
        body += "\n{{meeting_time}}"

    # Generate link URL
    link_url = (
        f"/project/workspace/{event.project_id}?tab=meetings"
        if event.project_id
        else "/dashboard?tab=meetings"
    )

    # Insert notification
    success = db.insert_notification(
        user_id=invited_user_id,
        event_id=event.id,
        title=title,
        body=body,
        link_url=link_url,
        payload={
            "type": "meeting_invitation",
            "meeting_id": event.meeting_id,
            "meeting_title": meeting_title,
            "start_time": start_time,
            "organizer_id": event.actor_id,
            "organizer_name": organizer_name,
            "project_id": event.project_id,
            "project_name": project_name,
        },
    )

    return HandlerResult(inserted=1 if success else 0)


def handle_meeting_update(db: Database, event: DomainEvent) -> HandlerResult:
    """Handle meeting_updated event."""
    logger.info(
        "Processing meeting_updated event: %d, meeting_id: %s",
        event.id,
        event.meeting_id,
    )

    if not event.meeting_id:
        logger.error("Missing meeting_id")
        return HandlerResult(inserted=0, reason="missing_meeting_id")

    # Get all participants except organizer
    participants = db.get_meeting_participants(event.meeting_id, exclude_user_id=event.actor_id)

    if not participants:
        logger.info("No participants to notify")
        return HandlerResult(inserted=0, reason="no_participants")

    # Get organizer name
    organizer_name = db.get_profile_name(event.actor_id)

    # Extract meeting details
    meeting_title = event.payload.get("meeting_title") or "a meeting"
    start_time = event.payload.get("start_time")
    changes = event.payload.get("changes") or {}

    # Get project name
    project_name = db.get_project_name(event.project_id) if event.project_id else None

    # Build notification
    title = (
        f"{organizer_name} updated a meeting - {project_name}"
        if project_name
        else f"{organizer_name} updated a meeting"
    )

    body = f"**{meeting_title}**"
    if start_time:
        body += "\nNew time: {{meeting_time}}"
    if changes.get("timeChanged"):
        body += "\n Time has been changed"
    if changes.get("participantsChanged"):
        body += "\n Participants updated"

    # Generate link URL
    link_url = (
        f"/project/workspace/{event.project_id}?tab=meetings"
        if event.project_id
        else "/dashboard?tab=meetings"
    )

    inserted_count = 0
    already_notified = db.get_existing_notification_recipients(event.id)

    for participant in participants:
        user_id = participant.get("user_id")
        if not user_id or user_id in already_notified:
            continue

        # Check preferences
        scope_type = "project" if event.project_id else "global"
        is_muted = db.check_user_preference_muted(
            user_id=user_id,
            scope_type=scope_type,
            scope_id=event.project_id or "",
            event_type="meeting_updated",
            channel="in_app",
            project_id=event.project_id or "",
        )

        if is_muted:
            continue

        # Insert notification
        if db.insert_notification(
            user_id=user_id,
            event_id=event.id,
            title=title,
            body=body,
            link_url=link_url,
            payload={
                "type": "meeting_update",
                "meeting_id": event.meeting_id,
                "meeting_title": meeting_title,
                "start_time": start_time,
                "organizer_id": event.actor_id,
                "organizer_name": organizer_name,
                "project_id": event.project_id,
                "project_name": project_name,
                "changes": changes,
            },
        ):
            inserted_count += 1

    return HandlerResult(inserted=inserted_count)


def handle_meeting_reminder(db: Database, event: DomainEvent) -> HandlerResult:
    """Handle meeting_reminder event."""
    logger.info(
        "Processing meeting_reminder event: %d, meeting_id: %s",
        event.id,
        event.meeting_id,
    )

    if not event.meeting_id:
        logger.error("Missing meeting_id")
        return HandlerResult(inserted=0, reason="missing_meeting_id")

    user_id = event.payload.get("user_id")
    if not user_id:
        logger.error("Missing user_id in payload")
        return HandlerResult(inserted=0, reason="missing_user_id")

    # Check for existing notification
    already_notified = db.get_existing_notification_recipients(event.id)
    if user_id in already_notified:
        return HandlerResult(inserted=0, reason="already_notified")

    # Check preferences
    scope_type = "project" if event.project_id else "global"
    is_muted = db.check_user_preference_muted(
        user_id=user_id,
        scope_type=scope_type,
        scope_id=event.project_id or "",
        event_type="meeting_reminder",
        channel="in_app",
        project_id=event.project_id or "",
    )

    if is_muted:
        return HandlerResult(inserted=0, reason="user_muted")

    # Extract meeting details
    meeting_title = event.payload.get("meeting_title") or "a meeting"
    start_time = event.payload.get("start_time")
    meeting_link = event.payload.get("meeting_link")
    reminder_minutes = event.payload.get("reminder_minutes") or 30

    # Format time display
    time_display = ""
    if start_time:
        from datetime import datetime

        try:
            dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            time_display = dt.strftime("%I:%M %p")
        except Exception:
            pass

    # Get project name
    project_name = db.get_project_name(event.project_id) if event.project_id else None

    # Build notification
    title = f"Reminder: Meeting in {reminder_minutes} minutes"

    body = f"**{meeting_title}**"
    if time_display:
        body += f"\nStarts at {time_display}"
    if project_name:
        body += f"\n{project_name}"

    # Generate link URL
    link_url = (
        f"/project/workspace/{event.project_id}?tab=meetings"
        if event.project_id
        else "/dashboard?tab=meetings"
    )

    # Insert notification
    success = db.insert_notification(
        user_id=user_id,
        event_id=event.id,
        title=title,
        body=body,
        link_url=link_url,
        payload={
            "type": "meeting_reminder",
            "meeting_id": event.meeting_id,
            "meeting_title": meeting_title,
            "start_time": start_time,
            "meeting_link": meeting_link,
            "project_id": event.project_id,
            "project_name": project_name,
            "reminder_minutes": reminder_minutes,
        },
    )

    return HandlerResult(inserted=1 if success else 0)


def handle_resume_incomplete_nudge(db: Database, event: DomainEvent) -> HandlerResult:
    """Handle resume_incomplete_nudge event."""
    logger.info(
        "Processing resume_incomplete_nudge event: %d, project_id: %s",
        event.id,
        event.project_id,
    )

    if not event.project_id:
        logger.error("Missing project_id")
        return HandlerResult(inserted=0, reason="missing_project_id")

    resume_type = event.payload.get("resume_type")
    completion_percent = event.payload.get("completion_percent")
    nudge_tier = event.payload.get("nudge_tier")
    user_id = event.payload.get("user_id")

    if resume_type is None or completion_percent is None or nudge_tier is None or user_id is None:
        logger.error("Missing required payload fields")
        return HandlerResult(inserted=0, reason="missing_payload_fields")

    # Get project owner org
    owner_org_id = db.get_project_owner_org(event.project_id)
    if not owner_org_id:
        logger.error("Could not find project owner org")
        return HandlerResult(inserted=0, reason="project_not_found")

    # Get project name
    project_name = db.get_project_name(event.project_id)

    # Verify user is an owner
    if not db.check_user_is_org_owner(owner_org_id, user_id):
        logger.info("User %s is not a project owner, skipping", user_id)
        return HandlerResult(inserted=0, reason="user_not_owner")

    # Check if notification already exists for this event
    if db.check_notification_exists(user_id, event.id):
        logger.info("Notification already exists for user %s and event %d", user_id, event.id)
        return HandlerResult(inserted=0, reason="already_notified")

    # Check if tier notification already exists
    if db.check_tier_notification_exists(user_id, resume_type, nudge_tier, event.project_id):
        logger.info("Tier %d nudge already sent to user %s", nudge_tier, user_id)
        return HandlerResult(inserted=0, reason="tier_already_sent")

    # Build notification
    resume_type_label = "Project" if resume_type == "project" else "Borrower"
    title = f"Complete your {resume_type_label} Resume"
    body = f"Your {resume_type_label} resume for **{project_name}** is **{completion_percent}%** complete. Finish it to generate your OM!"

    link_url = f"/project/workspace/{event.project_id}"

    # Insert notification
    success = db.insert_notification(
        user_id=user_id,
        event_id=event.id,
        title=title,
        body=body,
        link_url=link_url,
        payload={
            "type": "resume_incomplete_nudge",
            "resume_type": resume_type,
            "completion_percent": completion_percent,
            "nudge_tier": nudge_tier,
            "project_id": event.project_id,
            "project_name": project_name,
        },
    )

    if success:
        logger.info("Created resume nudge notification for user %s, tier %d", user_id, nudge_tier)

    return HandlerResult(inserted=1 if success else 0)


# Handler dispatch map
EVENT_HANDLERS = {
    "document_uploaded": handle_document_upload,
    "chat_message_sent": handle_chat_message,
    "meeting_invited": handle_meeting_invitation,
    "meeting_updated": handle_meeting_update,
    "meeting_reminder": handle_meeting_reminder,
    "resume_incomplete_nudge": handle_resume_incomplete_nudge,
}


def dispatch_event(db: Database, event: DomainEvent) -> HandlerResult:
    """Dispatch an event to the appropriate handler."""
    handler = EVENT_HANDLERS.get(event.event_type)

    if not handler:
        return HandlerResult(skipped=True, reason="unsupported_event_type")

    return handler(db, event)

