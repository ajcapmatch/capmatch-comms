"""Database operations using Supabase Python SDK."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set

from supabase import create_client, Client
from supabase.client import ClientOptions

logger = logging.getLogger(__name__)


class DomainEvent:
    """Typed representation of a domain event."""

    def __init__(self, data: Dict[str, Any]):
        self.id: int = data["id"]
        self.event_type: str = data["event_type"]
        self.actor_id: Optional[str] = data.get("actor_id")
        self.project_id: str = data["project_id"]
        self.resource_id: Optional[str] = data.get("resource_id")
        self.thread_id: Optional[str] = data.get("thread_id")
        self.meeting_id: Optional[str] = data.get("meeting_id")
        self.occurred_at: str = data["occurred_at"]
        self.payload: Dict[str, Any] = data.get("payload") or {}

        # Joined data from related tables
        projects = data.get("projects") or {}
        resources = data.get("resources") or {}
        self.owner_org_id: Optional[str] = projects.get("owner_org_id")
        self.resource_org_id: Optional[str] = resources.get("org_id")


class Database:
    """Database connection manager using Supabase client."""

    def __init__(self, supabase_url: str, supabase_key: str):
        self.client: Client = create_client(
            supabase_url,
            supabase_key,
            options=ClientOptions(
                postgrest_client_timeout=30,
                storage_client_timeout=30,
            ),
        )

    def get_domain_event(self, event_id: int) -> Optional[DomainEvent]:
        """Fetch a domain event by ID with related project and resource data."""
        response = (
            self.client.table("domain_events")
            .select(
                """
                id,
                event_type,
                actor_id,
                project_id,
                resource_id,
                thread_id,
                meeting_id,
                occurred_at,
                payload,
                projects!domain_events_project_id_fkey(owner_org_id),
                resources:resources!domain_events_resource_id_fkey(org_id)
                """
            )
            .eq("id", event_id)
            .maybe_single()
            .execute()
        )

        if not response.data:
            return None

        return DomainEvent(response.data)

    def get_unprocessed_events(self, limit: int = 100) -> List[DomainEvent]:
        """
        Fetch domain events that haven't been processed yet.
        Returns events where processed_at IS NULL, ordered by id ascending.
        """
        try:
            response = (
                self.client.table("domain_events")
                .select(
                    """
                    id,
                    event_type,
                    actor_id,
                    project_id,
                    resource_id,
                    thread_id,
                    meeting_id,
                    occurred_at,
                    payload,
                    projects!domain_events_project_id_fkey(owner_org_id),
                    resources:resources!domain_events_resource_id_fkey(org_id)
                    """
                )
                .is_("processed_at", "null")
                .order("id", desc=False)
                .limit(limit)
                .execute()
            )

            if not response.data:
                return []

            return [DomainEvent(row) for row in response.data]
        except Exception as e:
            logger.error("Failed to fetch unprocessed events: %s", e)
            return []

    def mark_event_processed(self, event_id: int) -> bool:
        """
        Mark a domain event as processed by setting processed_at to NOW().
        Returns True on success.
        """
        try:
            self.client.table("domain_events").update(
                {"processed_at": "now()"}
            ).eq("id", event_id).execute()
            return True
        except Exception as e:
            logger.error("Failed to mark event %d as processed: %s", event_id, e)
            return False

    def get_profile_name(self, user_id: Optional[str]) -> str:
        """Get display name for a user."""
        if not user_id:
            return "Someone"

        try:
            response = (
                self.client.table("profiles")
                .select("full_name, email")
                .eq("id", user_id)
                .maybe_single()
                .execute()
            )

            data = getattr(response, "data", None)
            if not data:
                return "Someone"

            return data.get("full_name") or data.get("email") or "Someone"
        except Exception as e:
            logger.error("get_profile_name failed for user=%s: %s", user_id, e)
            return "Someone"

    def get_project_name(self, project_id: str) -> str:
        """Get project name by ID."""
        try:
            response = (
                self.client.table("projects")
                .select("name")
                .eq("id", project_id)
                .maybe_single()
                .execute()
            )

            data = getattr(response, "data", None)
            if not data:
                return "Project"

            return data.get("name") or "Project"
        except Exception as e:
            logger.error("get_project_name failed for project=%s: %s", project_id, e)
            return "Project"

    def get_thread_info(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get thread information."""
        try:
            response = (
                self.client.table("chat_threads")
                .select("id, topic, project_id")
                .eq("id", thread_id)
                .maybe_single()
                .execute()
            )
            return getattr(response, "data", None)
        except Exception as e:
            logger.error("get_thread_info failed for thread=%s: %s", thread_id, e)
            return None

    def get_thread_participants(self, thread_id: str) -> List[Dict[str, str]]:
        """Get all participants in a thread."""
        try:
            response = (
                self.client.table("chat_thread_participants")
                .select("user_id")
                .eq("thread_id", thread_id)
                .execute()
            )
            return getattr(response, "data", None) or []
        except Exception as e:
            logger.error("get_thread_participants failed for thread=%s: %s", thread_id, e)
            return []

    def get_meeting_participants(
        self, meeting_id: str, exclude_user_id: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Get all participants in a meeting, optionally excluding a user."""
        try:
            query = self.client.table("meeting_participants").select("user_id").eq("meeting_id", meeting_id)

            if exclude_user_id:
                query = query.neq("user_id", exclude_user_id)

            response = query.execute()
            return getattr(response, "data", None) or []
        except Exception as e:
            logger.error("get_meeting_participants failed for meeting=%s: %s", meeting_id, e)
            return []

    def collect_candidate_user_ids(self, event: DomainEvent) -> Set[str]:
        """
        Collect all candidate user IDs who might receive notifications.
        Includes project access grants and org owners.
        """
        ids: Set[str] = set()

        try:
            # Get project access grants
            grants_response = (
                self.client.table("project_access_grants")
                .select("user_id")
                .eq("project_id", event.project_id)
                .execute()
            )

            for row in getattr(grants_response, "data", None) or []:
                if row.get("user_id"):
                    ids.add(row["user_id"])

            # Get org owners
            org_id = event.resource_org_id or event.owner_org_id
            if org_id:
                owners_response = (
                    self.client.table("org_members")
                    .select("user_id")
                    .eq("org_id", org_id)
                    .eq("role", "owner")
                    .execute()
                )

                for row in getattr(owners_response, "data", None) or []:
                    if row.get("user_id"):
                        ids.add(row["user_id"])
        except Exception as e:
            logger.error("collect_candidate_user_ids failed for event=%s: %s", event.id, e)

        return ids

    def filter_by_resource_access(
        self, candidate_ids: Set[str], resource_id: Optional[str]
    ) -> List[str]:
        """Filter user IDs by resource view access."""
        if not resource_id:
            return list(candidate_ids)

        results: List[str] = []
        for user_id in candidate_ids:
            try:
                response = self.client.rpc(
                    "can_view",
                    {"p_user_id": user_id, "p_resource_id": resource_id},
                ).execute()

                if getattr(response, "data", None) is True:
                    results.append(user_id)
            except Exception as e:
                logger.error("filter_by_resource_access failed for user=%s resource=%s: %s", user_id, resource_id, e)

        return results

    def get_existing_notification_recipients(self, event_id: int) -> Set[str]:
        """Get user IDs who already have notifications for this event."""
        try:
            response = (
                self.client.table("notifications")
                .select("user_id")
                .eq("event_id", event_id)
                .execute()
            )

            data = getattr(response, "data", None) or []
            return {row["user_id"] for row in data if row.get("user_id")}
        except Exception as e:
            logger.error("get_existing_notification_recipients failed for event=%s: %s", event_id, e)
            return set()

    def check_user_preference_muted(
        self,
        user_id: str,
        scope_type: str,
        scope_id: str,
        event_type: str,
        channel: str,
        project_id: str,
    ) -> bool:
        """
        Check if a user has muted notifications for a specific scope/event.
        Returns True if muted.

        Hierarchy: Thread > Project > Global
        """
        try:
            response = (
                self.client.table("user_notification_preferences")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )

            prefs = getattr(response, "data", None) or []
            if not prefs:
                return False  # Default: not muted
        except Exception as e:
            logger.error("check_user_preference_muted failed for user=%s: %s", user_id, e)
            return False  # Default: not muted on error

        # Filter relevant preferences
        relevant = [
            p
            for p in prefs
            if (p.get("event_type") == event_type or p.get("event_type") == "*")
            and (p.get("channel") == channel or p.get("channel") == "*")
        ]

        # Check Thread
        thread_pref = next(
            (p for p in relevant if p.get("scope_type") == "thread" and p.get("scope_id") == scope_id),
            None,
        )
        if thread_pref:
            return thread_pref.get("status") == "muted"

        # Check Project
        project_pref = next(
            (p for p in relevant if p.get("scope_type") == "project" and p.get("scope_id") == project_id),
            None,
        )
        if project_pref:
            return project_pref.get("status") == "muted"

        # Check Global
        global_pref = next((p for p in relevant if p.get("scope_type") == "global"), None)
        if global_pref:
            return global_pref.get("status") == "muted"

        return False

    def insert_notification(
        self,
        user_id: str,
        event_id: int,
        title: str,
        body: str,
        link_url: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Insert a notification. Returns True on success."""
        try:
            data = {
                "user_id": user_id,
                "event_id": event_id,
                "title": title,
                "body": body,
                "link_url": link_url,
            }
            if payload:
                data["payload"] = payload

            self.client.table("notifications").insert(data).execute()
            return True
        except Exception as e:
            logger.error("Failed to insert notification: %s", e)
            return False

    def insert_notifications_batch(
        self,
        rows: List[Dict[str, Any]],
    ) -> int:
        """Insert multiple notifications. Returns count of inserted rows."""
        if not rows:
            return 0

        try:
            self.client.table("notifications").insert(rows).execute()
            return len(rows)
        except Exception as e:
            logger.error("Failed to insert notifications batch: %s", e)
            return 0

    def get_unread_thread_notification(
        self, user_id: str, thread_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get existing unread notification for a thread."""
        try:
            response = (
                self.client.table("notifications")
                .select("id, payload")
                .eq("user_id", user_id)
                .is_("read_at", "null")
                .eq("payload->>thread_id", thread_id)
                .eq("payload->>type", "thread_activity")
                .order("created_at", desc=True)
                .limit(1)
                .maybe_single()
                .execute()
            )
            return getattr(response, "data", None)
        except Exception as e:
            logger.error(
                "get_unread_thread_notification failed for user=%s thread=%s: %s",
                user_id,
                thread_id,
                e,
            )
            return None

    def increment_notification_count(self, notification_id: str) -> bool:
        """Increment the count in a notification's payload."""
        try:
            self.client.rpc(
                "increment_notification_count",
                {"p_notification_id": notification_id},
            ).execute()
            return True
        except Exception as e:
            logger.error("Failed to increment notification count: %s", e)
            return False

    def get_project_owner_org(self, project_id: str) -> Optional[str]:
        """Get the owner org ID for a project."""
        try:
            response = (
                self.client.table("projects")
                .select("owner_org_id")
                .eq("id", project_id)
                .maybe_single()
                .execute()
            )

            data = getattr(response, "data", None)
            if not data:
                return None

            return data.get("owner_org_id")
        except Exception as e:
            logger.error("get_project_owner_org failed for project=%s: %s", project_id, e)
            return None

    def check_user_is_org_owner(self, org_id: str, user_id: str) -> bool:
        """Check if a user is an owner of an org."""
        try:
            response = (
                self.client.table("org_members")
                .select("user_id")
                .eq("org_id", org_id)
                .eq("role", "owner")
                .eq("user_id", user_id)
                .maybe_single()
                .execute()
            )
            return getattr(response, "data", None) is not None
        except Exception as e:
            logger.error("check_user_is_org_owner failed for org=%s user=%s: %s", org_id, user_id, e)
            return False

    def check_notification_exists(
        self,
        user_id: str,
        event_id: int,
    ) -> bool:
        """Check if a notification already exists for user/event."""
        try:
            response = (
                self.client.table("notifications")
                .select("id")
                .eq("user_id", user_id)
                .eq("event_id", event_id)
                .maybe_single()
                .execute()
            )
        except Exception as e:
            logger.error(
                "check_notification_exists failed for user=%s event_id=%s: %s",
                user_id,
                event_id,
                e,
            )
            return False

        return bool(getattr(response, "data", None))

    def check_tier_notification_exists(
        self,
        user_id: str,
        resume_type: str,
        nudge_tier: int,
        project_id: str,
    ) -> bool:
        """Check if a tier nudge notification already exists."""
        try:
            response = (
                self.client.table("notifications")
                .select("id")
                .eq("user_id", user_id)
                .eq("payload->>type", "resume_incomplete_nudge")
                .eq("payload->>resume_type", resume_type)
                .eq("payload->>nudge_tier", str(nudge_tier))
                .eq("payload->>project_id", project_id)
                .maybe_single()
                .execute()
            )
        except Exception as e:
            logger.error(
                "check_tier_notification_exists failed for user=%s resume_type=%s "
                "tier=%s project_id=%s: %s",
                user_id,
                resume_type,
                nudge_tier,
                project_id,
                e,
            )
            return False

        return bool(getattr(response, "data", None))

