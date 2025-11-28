"""Utility script to test Resend email delivery without running the full worker."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure the parent directory (service root) is importable.
PARENT_DIR = Path(__file__).resolve().parents[1]
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from datetime import datetime, timezone
from email_builder import build_digest_email  # noqa: E402
from email_sender import send_digest_email  # noqa: E402

SCENARIOS = {
    "delivered": "delivered@resend.dev",
    "bounced": "bounced@resend.dev",
    "complained": "complained@resend.dev",
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send a sample email via Resend using sandbox recipients."
    )
    parser.add_argument(
        "--scenario",
        choices=SCENARIOS.keys(),
        default="delivered",
        help="Resend sandbox behavior to exercise.",
    )
    args = parser.parse_args()

    recipient = SCENARIOS[args.scenario]
    print(f"Sending digest sample to {recipient} (scenario={args.scenario})")

    sample_events = [
        {
            "id": 1,
            "project_id": "project-1",
            "event_type": "chat_message_sent",
            "payload": {"mentioned_user_ids": []},
        },
        {
            "id": 2,
            "project_id": "project-1",
            "event_type": "document_uploaded",
        },
        {
            "id": 3,
            "project_id": "project-2",
            "event_type": "chat_message_sent",
            "payload": {"mentioned_user_ids": ["tester"]},
        },
    ]
    project_names = {
        "project-1": "Downtown Highrise Acquisition",
        "project-2": "Seaside Retail Portfolio",
    }

    html_body, text_body = build_digest_email(
        events=sample_events,
        user_name="CapMatch Tester",
        project_names=project_names,
        user_id="tester",
        digest_date=datetime.now(timezone.utc),
    )

    success = send_digest_email(
        user_email=recipient,
        user_name="CapMatch Tester",
        html_body=html_body,
        text_body=text_body,
        event_count=3,
    )

    if success:
        print("Resend accepted the message.")
    else:
        print("Resend reported a failure. Check logs for details.")


if __name__ == "__main__":
    main()

