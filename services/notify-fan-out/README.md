# Notify Fan-Out Service

A GCP Cloud Run service that receives webhooks from Supabase `domain_events` table and creates notifications in the `notifications` table.

This service replaces the Supabase Edge Function implementation, providing better scalability, observability, and deployment flexibility on GCP.

## Features

- **Event-driven notifications**: Processes domain events and creates in-app notifications
- **Preference-aware**: Respects user notification preferences (muted threads/projects)
- **Deduplication**: Prevents duplicate notifications for the same event
- **Aggregation**: Aggregates chat messages into single notifications per thread

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
| `PORT` | No | Server port (default: 8080) |
| `HOST` | No | Server host (default: 0.0.0.0) |
| `WEBHOOK_SECRET` | No | Optional shared secret for webhook auth |
| `LOG_LEVEL` | No | Logging level (default: INFO) |
| `APP_BASE_URL` | No | Base URL for notification links |

## API Endpoints

### `GET /`
Health check endpoint.

### `POST /webhook`
Main webhook endpoint for processing domain events.

**Request Body:**
```json
{
  "eventId": 123
}
```

**Response:**
```json
{
  "inserted": 5,
  "updated": 2
}
```

## Local Development

1. Create a `.env` file:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
LOG_LEVEL=DEBUG
```

2. Run the development server:
```bash
./scripts/run-dev.sh
```

Or manually:
```bash
uv sync
uv run python main.py
```

## Docker

Build and run with Docker:
```bash
./scripts/run-docker.sh
```

Or manually:
```bash
# From repo root
docker build -f services/notify-fan-out/Dockerfile -t notify-fan-out .
docker run --env-file services/notify-fan-out/.env -p 8080:8080 notify-fan-out
```

## Deployment

### Manual Deploy to Cloud Run

```bash
./scripts/deploy.sh <PROJECT_ID> [REGION]
```

### Cloud Build

Trigger a build with Cloud Build:
```bash
gcloud builds submit --config services/notify-fan-out/cloudbuild.yaml .
```

### Set Environment Variables

After deployment, set the required environment variables:
```bash
gcloud run services update notify-fan-out \
  --region us-west1 \
  --set-env-vars SUPABASE_URL=<url>,SUPABASE_SERVICE_ROLE_KEY=<key>
```

## Supabase Webhook Configuration

Configure a database webhook in Supabase to call this service when new events are inserted into `domain_events`:

1. Go to Supabase Dashboard → Database → Webhooks
2. Create new webhook:
   - **Name**: `notify-fan-out`
   - **Table**: `domain_events`
   - **Events**: `INSERT`
   - **Type**: HTTP Request
   - **Method**: POST
   - **URL**: `https://notify-fan-out-xxx.run.app/webhook`
   - **Headers**: 
     - `Authorization: Bearer <your-webhook-secret>` (if using WEBHOOK_SECRET)
     - `Content-Type: application/json`
   - **Body**: 
     ```json
     {
       "eventId": "{{new.id}}"
     }
     ```

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  domain_events  │────▶│  notify-fan-out  │────▶│  notifications  │
│     (insert)    │     │   (Cloud Run)    │     │    (insert)     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │
         │                       ▼
         │              ┌────────────────┐
         └──────────────│ Supabase DB    │
                        │ - profiles     │
                        │ - projects     │
                        │ - preferences  │
                        └────────────────┘
```

## Migration from Edge Functions

This service is a 1:1 replacement for the Supabase Edge Function. The main differences:

1. **Runtime**: Deno → Python 3.13
2. **Framework**: Native fetch → Flask
3. **Supabase Client**: JavaScript SDK → Python SDK
4. **Deployment**: Supabase Edge → GCP Cloud Run

All business logic, notification formats, and database queries remain identical.

