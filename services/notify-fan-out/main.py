"""
Notify Fan-Out Service

Processes unprocessed domain_events from Supabase and creates
notifications in the notifications table.

This script runs once and exits. It should be called periodically
by a cron job or Cloud Scheduler.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone

from config import Config
from database import Database, DomainEvent
from handlers import dispatch_event

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Force unbuffered output for container logs
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

logger = logging.getLogger(__name__)

# Reduce noise from httpx and httpcore
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def process_event(db: Database, event: DomainEvent) -> bool:
    """
    Process a single domain event.
    
    Returns True if successfully processed, False otherwise.
    """
    try:
        logger.info(
            "Processing event: id=%d, type=%s, project=%s",
            event.id,
            event.event_type,
            event.project_id,
        )

        # Dispatch to appropriate handler
        result = dispatch_event(db, event)

        logger.info(
            "Event processed: id=%d, result=%s",
            event.id,
            result.to_dict(),
        )

        # Mark as processed regardless of handler result
        # (we don't want to reprocess events that were skipped intentionally)
        if not db.mark_event_processed(event.id):
            logger.error("Failed to mark event %d as processed", event.id)
            return False

        return True

    except Exception as e:
        logger.exception("Error processing event %d: %s", event.id, e)
        return False


def main():
    """Main execution function."""
    start_time = datetime.now(timezone.utc)
    logger.info("=" * 80)
    logger.info("Starting Notify Fan-Out Job")
    logger.info(f"Started at: {start_time.isoformat()}")
    logger.info("=" * 80)

    try:
        # Validate configuration
        Config.validate()
        logger.info("Configuration validated")

        # Initialize database
        db = Database(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_ROLE_KEY)
        logger.info("Connected to Supabase at %s", Config.SUPABASE_URL)

        # Process events in batches
        processed = 0
        failed = 0
        batch_size = 100

        while True:
            events = db.get_unprocessed_events(limit=batch_size)
            
            if not events:
                logger.info("No unprocessed events found")
                break

            logger.info("Found %d unprocessed event(s)", len(events))

            for event in events:
                if process_event(db, event):
                    processed += 1
                else:
                    failed += 1

            # If we got fewer events than the batch size, we're done
            if len(events) < batch_size:
                break

        # Summary
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        logger.info("=" * 80)
        logger.info("Notify Fan-Out Job completed")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Events processed: {processed}")
        logger.info(f"Events failed: {failed}")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Fatal error in notify fan-out job: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
