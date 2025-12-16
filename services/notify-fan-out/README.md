# Notify Fan-Out Service

A cron job that processes unprocessed domain events from Supabase and creates notifications in the `notifications` table.

This service runs once per execution and is scheduled by a system cron job to run every minute on a VM.

## Features

- **Cron-based**: Runs on a schedule via system cron (every minute)
- **Event-driven notifications**: Processes domain events and creates in-app notifications
- **Preference-aware**: Respects user notification preferences (muted threads/projects)
- **Deduplication**: Prevents duplicate notifications for the same event
- **Aggregation**: Aggregates chat messages into single notifications per thread
- **Batch processing**: Processes events in batches of 100

## Supported Events

| Event Type | Description |
|------------|-------------|
| `document_uploaded` | New document uploaded to a project |
| `chat_message_sent` | New message in a chat thread |
| `meeting_invited` | User invited to a meeting |
| `meeting_updated` | Meeting details changed |
| `meeting_reminder` | Upcoming meeting reminder |
| `resume_incomplete_nudge` | Nudge to complete resume |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Supabase service role key |
| `LOG_LEVEL` | No | Logging level (default: INFO) |
| `APP_BASE_URL` | No | Base URL for notification links |

## Database Migration

Before running the service, apply the migration to add the `processed_at` column:

```sql
-- Run this in Supabase SQL Editor
ALTER TABLE public.domain_events 
ADD COLUMN IF NOT EXISTS processed_at TIMESTAMPTZ DEFAULT NULL;

CREATE INDEX IF NOT EXISTS idx_domain_events_unprocessed 
ON public.domain_events (id) 
WHERE processed_at IS NULL;

-- Drop the webhook trigger (no longer needed)
DROP TRIGGER IF EXISTS "domain_events_webhook" ON "public"."domain_events";
```

Or run the migration file:
```bash
psql $DATABASE_URL < migrations/001_add_processed_at.sql
```

## Local Development

1. Create a `.env` file:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
LOG_LEVEL=DEBUG
```

2. Run the service once:
```bash
./scripts/run-dev.sh
```

Or manually:
```bash
uv sync
uv run python main.py
```

3. Set up a local cron job (optional):
```bash
./scripts/setup-cron.sh
```

This will add a cron entry to run the service every minute.

## Docker

Build and run with Docker:
```bash
./scripts/run-docker.sh
```

Or manually:
```bash
# From repo root
docker build -f services/notify-fan-out/Dockerfile -t notify-fan-out .
docker run --env-file services/notify-fan-out/.env notify-fan-out
```

## Deployment

### VM Deployment

1. **One-time VM setup:**
```bash
cd services/notify-fan-out
./setup-vm.sh
```

This will:
- Install Docker and dependencies
- Build the Docker image
- Set up a cron job to run every minute
- Create log file at `/var/log/notify-fan-out.log`

2. **Create `.env` file** with required variables:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
LOG_LEVEL=INFO
```

3. **Update after code changes:**
```bash
cd services/notify-fan-out
./deploy.sh
```

This will:
- Pull latest code from git
- Rebuild the Docker image

4. **Test manually:**
```bash
./run-notify-fan-out.sh
```

5. **View logs:**
```bash
tail -f /var/log/notify-fan-out.log
```

6. **View cron schedule:**
```bash
crontab -l
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Cron / Cloud Scheduler                   │
│                    (runs every minute)                      │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Notify Fan-Out Job (runs once)                  │
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ Fetch Events   │───▶│ Process Events │                │
│  │ (processed_at  │    │                 │                │
│  │  IS NULL)      │    │                 │                │
│  └─────────────────┘    └─────────────────┘                │
│       │                      │                               │
│       ▼                      ▼                               │
└───────┼──────────────────────┼───────────────────────────────┘
        │                      │
        ▼                      ▼
┌─────────────────────────────────────────────────────────────┐
│                        Supabase                             │
│                                                             │
│  ┌─────────────────┐         ┌─────────────────┐           │
│  │  domain_events  │         │  notifications  │           │
│  │                 │         │                 │           │
│  │ processed_at    │         │                 │           │
│  │ IS NULL = new   │         │                 │           │
│  └─────────────────┘         └─────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

## How It Works

1. **Cron/Scheduler**: Triggers the job every minute (or your configured schedule)
2. **Fetch**: Query `domain_events` where `processed_at IS NULL` (up to 100 at a time)
3. **Process**: For each event, dispatch to the appropriate handler based on `event_type`
4. **Notify**: Create notifications in the `notifications` table
5. **Mark**: Set `processed_at = NOW()` on the event to prevent reprocessing
6. **Exit**: Job completes and exits

## How It Works

The service runs as a cron job on a VM:
- Cron triggers `run-notify-fan-out.sh` every minute
- The script runs the service in a Docker container
- The service processes all unprocessed events and exits
- Logs are written to `/var/log/notify-fan-out.log`
