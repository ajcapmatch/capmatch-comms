"""Preference resolution logic for email digest."""

from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Event types that default to digest if no preference is set
DIGEST_DEFAULT_EVENTS = {'chat_message_sent', 'document_uploaded'}


def get_user_preferences(db, user_id: str) -> list:
    """Get all notification preferences for a user."""
    response = db.client.table('user_notification_preferences').select(
        '*'
    ).eq('user_id', user_id).execute()
    return response.data if response.data else []


def should_include_in_digest(
    db,
    event: Dict[str, Any],
    user_id: str
) -> bool:
    """
    Check if this event should be included in digest for this user.
    Uses preference hierarchy: thread > project > global > default
    
    Returns True if event should be included in digest, False otherwise.
    """
    preferences = get_user_preferences(db, user_id)
    
    if not preferences:
        # No preferences set - use defaults
        return event['event_type'] in DIGEST_DEFAULT_EVENTS
    
    event_type = event['event_type']
    
    # Filter relevant preferences (matching event_type and email channel)
    relevant = [
        p for p in preferences
        if (p['event_type'] == event_type or p['event_type'] == '*')
        and (p['channel'] == 'email' or p['channel'] == '*')
    ]
    
    if not relevant:
        # No matching preferences - use defaults
        return event['event_type'] in DIGEST_DEFAULT_EVENTS
    
    # Check hierarchy: thread > project > global
    # Thread-level preference
    if event.get('thread_id'):
        thread_pref = next(
            (p for p in relevant 
             if p['scope_type'] == 'thread' and p['scope_id'] == event['thread_id']),
            None
        )
        if thread_pref:
            return thread_pref['status'] == 'digest'
    
    # Project-level preference
    project_pref = next(
        (p for p in relevant 
         if p['scope_type'] == 'project' and p['scope_id'] == event['project_id']),
        None
    )
    if project_pref:
        return project_pref['status'] == 'digest'
    
    # Global preference
    global_pref = next(
        (p for p in relevant 
         if p['scope_type'] == 'global' and p['scope_id'] is None),
        None
    )
    if global_pref:
        return global_pref['status'] == 'digest'
    
    # No matching preference found - use defaults
    return event['event_type'] in DIGEST_DEFAULT_EVENTS


def filter_events_by_preferences(
    db,
    events: list,
    user_id: str
) -> list:
    """
    Filter events to only include those that should be in digest
    based on user preferences.
    """
    filtered_events = []

    for event in events:
        include = should_include_in_digest(db, event, user_id)
        logger.debug(
            "[preferences] user=%s event_id=%s event_type=%s include=%s thread=%s project=%s",
            user_id,
            event.get("id"),
            event.get("event_type"),
            include,
            event.get("thread_id"),
            event.get("project_id"),
        )
        if include:
            filtered_events.append(event)

    return filtered_events

