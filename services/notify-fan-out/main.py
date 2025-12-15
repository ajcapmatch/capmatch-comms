"""
Notify Fan-Out Service

Receives webhooks from Supabase domain_events table and creates
notifications in the notifications table.

This service replaces the Supabase Edge Function implementation.
"""

from __future__ import annotations

import logging
import sys

from flask import Flask, request, jsonify, Response
from typing import Any, Dict, Optional, Tuple

from config import Config
from database import Database
from handlers import dispatch_event, HandlerResult

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

app = Flask(__name__)

# Global database instance (initialized on first request)
_db: Optional[Database] = None


def get_db() -> Database:
    """Get or create database instance."""
    global _db
    if _db is None:
        Config.validate()
        _db = Database(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_ROLE_KEY)
        logger.info("Database connection initialized")
    return _db


def json_response(
    body: Dict[str, Any], status: int = 200
) -> Tuple[Response, int]:
    """Create a JSON response with CORS headers."""
    response = jsonify(body)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = (
        "authorization, x-client-info, apikey, content-type"
    )
    return response, status


def parse_event_id(value: Any) -> Optional[int]:
    """Parse event ID from a single value (int or string)."""
    if isinstance(value, int) and value > 0:
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = int(value)
            return parsed if parsed > 0 else None
        except ValueError:
            return None
    return None


def extract_event_id_from_body(body: Dict[str, Any]) -> Optional[int]:
    """
    Extract the domain_event ID from various payload shapes.

    Supported formats:
    1) { "eventId": 123 } or { "event_id": 123 }
    2) Supabase DB webhook style:
       {
         "type": "INSERT",
         "table": "domain_events",
         "record": { "id": 123, ... }
       }
    """
    # 1. Direct eventId / event_id
    direct = body.get("eventId") or body.get("event_id")
    event_id = parse_event_id(direct)
    if event_id:
        return event_id

    # 2. Supabase webhook style payload
    record = body.get("record")
    if isinstance(record, dict):
        event_id = parse_event_id(record.get("id"))
        if event_id:
            return event_id

    return None


@app.route("/", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return json_response({
        "status": "ok",
        "service": "notify-fan-out",
        "version": "1.0.0",
    })


@app.route("/", methods=["OPTIONS"])
@app.route("/webhook", methods=["OPTIONS"])
def handle_options():
    """Handle CORS preflight requests."""
    response = Response("ok")
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = (
        "authorization, x-client-info, apikey, content-type"
    )
    response.headers["Access-Control-Max-Age"] = "86400"
    return response


@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Main webhook endpoint for processing domain events.

    Expected payloads:
    1) Direct:
       { "eventId": <number> } or { "event_id": <number> }

    2) Supabase DB webhook:
       {
         "type": "INSERT",
         "table": "domain_events",
         "record": { "id": <number>, ... }
       }

    The service will:
    1. Fetch the domain event from Supabase
    2. Dispatch to the appropriate handler based on event_type
    3. Create notifications in the notifications table
    """
    try:
        # Validate authorization header (optional shared secret)
        # If WEBHOOK_SECRET is set, require a matching Bearer token.
        # If not set, allow requests without any Authorization header.
        auth_header = request.headers.get("Authorization")
        if Config.WEBHOOK_SECRET:
            expected = f"Bearer {Config.WEBHOOK_SECRET}"
            if auth_header != expected:
                logger.warning("Invalid or missing authorization header")
                return json_response({"error": "Unauthorized"}, 401)

        # Parse request body
        body = request.get_json(silent=True) or {}

        # Extract event ID from supported payload shapes
        event_id = extract_event_id_from_body(body)

        if not event_id:
            logger.warning("Missing or invalid eventId in request")
            return json_response({"error": "eventId is required"}, 400)

        logger.info("Processing event: %d", event_id)

        # Get database instance
        db = get_db()

        # Fetch the domain event
        event = db.get_domain_event(event_id)
        if not event:
            logger.warning("Event not found: %d", event_id)
            return json_response({"error": "domain_event not found"}, 404)

        logger.info(
            "Dispatching event: id=%d, type=%s, project=%s",
            event.id,
            event.event_type,
            event.project_id,
        )

        # Dispatch to handler
        result = dispatch_event(db, event)

        logger.info(
            "Event processed: id=%d, result=%s",
            event_id,
            result.to_dict(),
        )

        # Return appropriate status code
        if result.error:
            return json_response(result.to_dict(), 500)

        return json_response(result.to_dict())

    except Exception as e:
        logger.exception("Unexpected error processing webhook")
        return json_response(
            {"error": str(e) if str(e) else "Unknown error"},
            500,
        )


@app.route("/webhook", methods=["GET"])
def webhook_info():
    """Info endpoint for webhook."""
    return json_response({
        "status": "ok",
        "message": "Webhook endpoint is ready. Send POST requests here.",
        "method": "POST",
        "expected_payload": {
            "eventId": "<number>",
        },
        "supported_events": [
            "document_uploaded",
            "chat_message_sent",
            "meeting_invited",
            "meeting_updated",
            "meeting_reminder",
            "resume_incomplete_nudge",
        ],
    })


def main():
    """Run the Flask development server."""
    logger.info("=" * 80)
    logger.info("Starting Notify Fan-Out Service")
    logger.info("=" * 80)

    try:
        Config.validate()
        logger.info("Configuration validated")
    except ValueError as e:
        logger.error("Configuration error: %s", e)
        sys.exit(1)

    logger.info("Server running on: http://%s:%d", Config.HOST, Config.PORT)
    logger.info("Webhook endpoint: http://%s:%d/webhook", Config.HOST, Config.PORT)
    logger.info("=" * 80)

    # Disable Flask's default request logging in production
    import logging as flask_logging
    flask_logging.getLogger("werkzeug").setLevel(flask_logging.WARNING)

    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=False,
    )


if __name__ == "__main__":
    main()

