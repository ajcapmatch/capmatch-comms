# Email Digest Worker

Daily email digest service that sends aggregated notifications to users with digest preferences.

## Overview

This Cloud Run Job processes `domain_events` from the previous day and sends digest emails to users who have email digest notifications enabled.

## Architecture

- **Trigger**: Cloud Scheduler (daily at 9 AM PST)
- **Execution**: Cloud Run Job
- **Database**: Supabase PostgreSQL
- **Email**: Resend API (currently logging to console)

## Setup

### 1. Environment Variables

Set these in Cloud Run Job configuration or Secret Manager:

- `SUPABASE_URL`: Supabase project URL (e.g., `https://your-project.supabase.co`)
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role key (for admin access)
- `RESEND_API_KEY`: Resend API key (for future email sending)
- `EMAIL_FROM`: Sender email address (default: notifications@capmatch.com)
- `LOG_LEVEL`: Logging level (default: INFO)
- `SKIP_IDEMPOTENCY_CHECK`: Set to `true` while testing to reprocess the same events (default: false)

### 2. Build Docker Image

```bash
cd workers/email-digest
docker build -t gcr.io/PROJECT_ID/email-digest-worker .
docker push gcr.io/PROJECT_ID/email-digest-worker
```

### 3. Deploy Cloud Run Job

```bash
gcloud run jobs create email-digest-worker \
  --image gcr.io/PROJECT_ID/email-digest-worker \
  --region us-central1 \
  --set-env-vars SUPABASE_URL=$SUPABASE_URL \
  --set-secrets SUPABASE_SERVICE_ROLE_KEY=supabase-service-role-key:latest \
  --set-secrets RESEND_API_KEY=resend-api-key:latest \
  --max-retries 0 \
  --task-timeout 10m \
  --memory 512Mi \
  --cpu 1
```

### 4. Schedule with Cloud Scheduler

```bash
gcloud scheduler jobs create http email-digest-daily \
  --location us-central1 \
  --schedule "0 9 * * *" \
  --time-zone "America/Los_Angeles" \
  --uri "https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/PROJECT_ID/jobs/email-digest-worker:run" \
  --http-method POST \
  --oauth-service-account-email PROJECT_ID@appspot.gserviceaccount.com
```

## Local Development

### Setup

```bash
cd workers/email-digest
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run Locally

```bash
# Create .env.local file with your Supabase credentials
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
# LOG_LEVEL=DEBUG

# Run with uv (recommended)
uv run --env-file .env.local python main.py

# Or set environment variables manually
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
uv run python main.py
```

## How It Works

1. **Get Users**: Queries `user_notification_preferences` for users with `status='digest'` and `channel='email'`
2. **Get Events**: For each user, queries `domain_events` from yesterday that haven't been processed
3. **Filter Events**: 
   - Checks user preferences (thread > project > global hierarchy)
   - Verifies user is a recipient (project access, thread participant, etc.)
   - Checks resource access for document events
4. **Build Email**: Groups events by project and type, counts mentions
5. **Send Email**: Currently logs to console (will send via Resend when implemented)
6. **Mark Processed**: Inserts into `email_digest_processed` to prevent duplicates

## Database Schema

### `email_digest_processed`

Tracks which events have been included in digests:

- `event_id`: FK to `domain_events.id`
- `user_id`: FK to `profiles.id`
- `digest_date`: Date the digest was sent
- `sent_at`: Timestamp when processed

## Default Preferences

Default preferences are handled in application logic (not stored in database):
- If no preference row exists, these event types default to digest:
  - `chat_message_sent` (including mentions)
  - `document_uploaded`
- Defaults are defined in `preferences.py` as `DIGEST_DEFAULT_EVENTS`

## Monitoring

Check Cloud Run Job logs for:
- Users processed
- Events found per user
- Email send status (currently console logs)
- Errors and failures

## Troubleshooting

### Job fails to start
- Check `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are set correctly
- Verify Supabase URL format (should be `https://your-project.supabase.co`)
- Ensure service role key has admin access

### No users processed
- Check if users have digest preferences set
- Verify `user_notification_preferences` table has entries

### No events found
- Check `domain_events` table has events from yesterday
- Verify date calculation (UTC)

### Events not included
- Check user preferences match event types
- Verify user is a recipient (project access, thread participant)
- Check resource access for document events

