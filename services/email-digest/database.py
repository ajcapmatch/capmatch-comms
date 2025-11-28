"""Database connection and query functions using Supabase Python SDK."""

from supabase import create_client, Client
from typing import List, Dict, Any, Optional, Set
from datetime import date
import logging

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager using Supabase client."""
    
    def __init__(self, supabase_url: str, supabase_key: str, *, skip_idempotency: bool = False):
        self.client: Client = create_client(supabase_url, supabase_key)
        self.skip_idempotency = skip_idempotency
    
    def get_users_with_digest_preferences(self) -> List[Dict[str, Any]]:
        """
        Get all users who should receive digest emails.
        This includes:
        1. Users with explicit digest preferences for email channel
        2. All other users (they'll get defaults: chat_message_sent and document_uploaded)
        
        Returns list of users with their email addresses.
        """
        # Get all users (we'll filter for email in Python)
        users_response = self.client.table('profiles').select(
            'id, email, full_name'
        ).execute()
        
        if not users_response.data:
            return []
        
        # Filter to only users with emails
        users_with_emails = [u for u in users_response.data if u.get('email')]
        
        # Get users with digest preferences
        digest_prefs_response = self.client.table('user_notification_preferences').select(
            'user_id'
        ).in_('channel', ['email', '*']).eq('status', 'digest').execute()
        
        digest_user_ids = {p['user_id'] for p in digest_prefs_response.data}
        
        # Get all users with any email preferences
        all_email_prefs_response = self.client.table('user_notification_preferences').select(
            'user_id'
        ).in_('channel', ['email', '*']).execute()
        
        users_with_email_prefs = {p['user_id'] for p in all_email_prefs_response.data}
        
        # Return users with digest prefs OR users without any email prefs
        result = []
        for user in users_with_emails:
            if (
                user['id'] in digest_user_ids or 
                user['id'] not in users_with_email_prefs
            ):
                result.append({
                    'user_id': user['id'],
                    'email': user['email'],
                    'full_name': user.get('full_name')
                })
        
        return result
    
    def get_unprocessed_events(
        self, 
        user_id: str, 
        digest_date: date,
        start_time: str,
        end_time: str
    ) -> List[Dict[str, Any]]:
        """
        Get all events from digest_date that should be in digest for this user
        and haven't been processed yet.
        
        Returns events that:
        1. Occurred within the date range
        2. Haven't been processed for this user/date
        """
        query = self.client.table('domain_events').select('*')

        if not self.skip_idempotency:
            query = query.gte('occurred_at', start_time).lt('occurred_at', end_time)
        else:
            logger.debug(
                "[testing] SKIP_IDEMPOTENCY_CHECK true -> returning all domain events regardless of time"
            )

        events_response = query.order('occurred_at', desc=False).execute()
        events = events_response.data or []

        if self.skip_idempotency:
            logger.debug(
                "[idempotency] Skipping processed-event filtering for user %s (returning %d events)",
                user_id,
                len(events),
            )
            return events
        
        # Get processed events for this user/date
        processed_response = self.client.table('email_digest_processed').select(
            'event_id'
        ).eq('user_id', user_id).eq('digest_date', digest_date.isoformat()).execute()
        
        processed_event_ids = {p['event_id'] for p in (processed_response.data or [])}
        
        # Filter out processed events
        filtered = [
            event for event in events
            if event['id'] not in processed_event_ids
        ]

        logger.debug(
            "[idempotency] Filtered %d/%d events for user %s on %s",
            len(events) - len(filtered),
            len(events),
            user_id,
            digest_date,
        )
        
        return filtered
    
    def get_event_recipients(self, event: Dict[str, Any]) -> Set[str]:
        """
        Get list of user IDs who should receive this event.
        Reuses logic from notify-fan-out: project access grants + org owners + thread participants.
        """
        recipients = set()
        logger.debug(
            "[recipients] event_id=%s type=%s project=%s thread=%s resource=%s actor=%s",
            event.get("id"),
            event.get("event_type"),
            event.get("project_id"),
            event.get("thread_id"),
            event.get("resource_id"),
            event.get("actor_id"),
        )
        
        # Get project access grants
        grants_response = self.client.table('project_access_grants').select(
            'user_id'
        ).eq('project_id', event['project_id']).execute()
        
        for grant in grants_response.data:
            if grant.get('user_id'):
                recipients.add(grant['user_id'])
        
        # Get org owners if resource_id exists
        if event.get('resource_id'):
            # First get the resource's org_id
            resource_response = self.client.table('resources').select(
                'org_id'
            ).eq('id', event['resource_id']).single().execute()
            
            if resource_response.data and resource_response.data.get('org_id'):
                org_id = resource_response.data['org_id']
                owners_response = self.client.table('org_members').select(
                    'user_id'
                ).eq('org_id', org_id).eq('role', 'owner').execute()
                
                for owner in owners_response.data:
                    if owner.get('user_id'):
                        recipients.add(owner['user_id'])
        
        # Get thread participants if thread_id exists
        if event.get('thread_id'):
            participants_response = self.client.table('chat_thread_participants').select(
                'user_id'
            ).eq('thread_id', event['thread_id']).execute()
            
            for participant in participants_response.data:
                if participant.get('user_id'):
                    recipients.add(participant['user_id'])
        
        # Exclude actor
        if event.get('actor_id'):
            recipients.discard(event['actor_id'])
            logger.debug(
                "[recipients] removed actor %s from recipient list",
                event['actor_id']
            )
        
        logger.debug(
            "[recipients] final recipients for event %s: %s",
            event.get("id"),
            list(recipients),
        )
        return recipients
    
    def check_resource_access(self, user_id: str, resource_id: str) -> bool:
        """Check if user has view access to a resource using RPC function."""
        response = self.client.rpc(
            'can_view',
            {
                'p_user_id': user_id,
                'p_resource_id': resource_id
            }
        ).execute()
        
        return response.data if response.data else False
    
    def get_project_names(self, project_ids: List[str]) -> Dict[str, str]:
        """Batch fetch project names."""
        if not project_ids:
            return {}
        
        response = self.client.table('projects').select(
            'id, name'
        ).in_('id', project_ids).execute()
        
        return {row['id']: row['name'] for row in response.data}
    
    def mark_events_processed(
        self, 
        events: List[Dict[str, Any]], 
        user_id: str, 
        digest_date: date
    ) -> None:
        """Mark events as processed in email_digest_processed table."""
        if not events:
            return

        if self.skip_idempotency:
            logger.debug(
                "[idempotency] Skipping mark_events_processed for user %s (testing mode)",
                user_id,
            )
            return
        
        # Prepare data for batch insert
        records = [
            {
                'event_id': event['id'],
                'user_id': user_id,
                'digest_date': digest_date.isoformat()
            }
            for event in events
        ]
        
        # Insert records, ignoring duplicates (ON CONFLICT DO NOTHING behavior)
        # Supabase upsert with on_conflict parameter
        inserted = 0
        for record in records:
            try:
                self.client.table('email_digest_processed').upsert(
                    record,
                    on_conflict='event_id,user_id,digest_date'
                ).execute()
                inserted += 1
            except Exception as e:
                # If upsert fails (e.g., constraint violation), try insert and ignore duplicates
                try:
                    self.client.table('email_digest_processed').insert(record).execute()
                    inserted += 1
                except Exception:
                    # Ignore duplicate key errors (ON CONFLICT DO NOTHING behavior)
                    pass
        
        logger.info(f"Marked {inserted} events as processed for user {user_id}")
