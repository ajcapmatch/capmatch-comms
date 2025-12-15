# Testing Guide for Email Digest Service

This guide covers different ways to test the email digest service, from quick email delivery tests to full integration testing.

## Prerequisites

1. **Environment Variables**: Create a `.env.local` file (or `.env` for Docker) with:
   ```bash
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
   RESEND_API_KEY=your-resend-api-key
   EMAIL_FROM=notifications@capmatch.com
   LOG_LEVEL=DEBUG  # Use DEBUG for more verbose output
   ```

2. **Install Dependencies**:
   ```bash
   cd services/email-digest
   # Install Python dependencies using uv
   uv sync
   ```

3. **Build Email Templates** (if you've modified them):
   ```bash
   cd ../../packages/email-templates
   npm install
   npm run render  # Generates dist/digest-template.html
   ```

## Testing Methods

### 1. Quick Email Delivery Test (Resend Sandbox)

Test email sending without running the full worker or hitting your database:

```bash
cd services/email-digest
uv run --env-file .env.local python scripts/send_resend_test.py --scenario delivered
```

**Available scenarios:**
- `delivered` - Tests successful delivery (sends to `delivered@resend.dev`)
- `bounced` - Tests bounce handling (sends to `bounced@resend.dev`)
- `complained` - Tests complaint handling (sends to `complained@resend.dev`)

**What it does:**
- Creates sample events and project data
- Builds a digest email using the template
- Sends via Resend API to sandbox recipients
- No database queries, no real user data

**Environment variables for this test:**
```bash
RESEND_API_KEY=your-resend-api-key
EMAIL_FROM=notifications@capmatch.com
# Optional: override recipient
RESEND_TEST_RECIPIENT=your-test@email.com
RESEND_FORCE_TO_EMAIL=your-test@email.com
```

### 2. Local Development Testing (Full Worker)

Run the complete worker locally against your Supabase database:

```bash
cd services/email-digest

# Option 1: Using uv with env file
uv run --env-file .env.local python main.py

# Option 2: Export environment variables manually
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
export RESEND_API_KEY="your-resend-api-key"
export EMAIL_FROM="notifications@capmatch.com"
export LOG_LEVEL="DEBUG"
uv run python main.py
```

**What it does:**
- Connects to Supabase
- Queries users with digest preferences
- Fetches unprocessed events from the last 24 hours
- Filters events by preferences and recipient status
- Builds and sends emails via Resend
- Marks events as processed

**Testing Tips:**
- Set `LOG_LEVEL=DEBUG` to see detailed logs
- Set `SKIP_IDEMPOTENCY_CHECK=true` to reprocess the same events (useful for testing)
- Use `RESEND_TEST_MODE=true` to send to test recipients instead of real users
- Use `RESEND_FORCE_TO_EMAIL=your-test@email.com` to redirect all emails to one address

### 3. Docker-Based Testing

Test using Docker (closest to production environment):

```bash
cd services/email-digest

# Build the Docker image (from repo root)
cd ../..
docker build -f services/email-digest/Dockerfile -t capmatch-email-digest:prod .

# Run the container
cd services/email-digest
docker run --rm --env-file .env capmatch-email-digest:prod
```

**Or use the convenience script:**
```bash
cd services/email-digest
chmod +x run-email-digest.sh
./run-email-digest.sh
```

This will:
- Build the image if needed
- Run the container with your `.env` file
- Log output to `/var/log/email-digest.log` (or stdout if not writable)

### 4. Template Testing

Test and preview email templates without sending:

```bash
cd packages/email-templates

# Preview templates in browser (live reload)
npm run preview

# Render templates to HTML files
npm run render

# Render with sample data
USE_SAMPLE_DATA=true npm run render
```

The preview server opens at `http://localhost:3000` and shows both templates with sample data.

### 5. Integration Testing Checklist

To test the full flow end-to-end:

1. **Setup Test Data in Supabase:**
   - Create a test user with digest preferences enabled
   - Create some `domain_events` in the last 24 hours
   - Ensure the user is a recipient of those events

2. **Run with Test Mode:**
   ```bash
   export RESEND_TEST_MODE=true
   export RESEND_TEST_RECIPIENT=your-test@email.com
   export SKIP_IDEMPOTENCY_CHECK=true  # To reprocess same events
   export LOG_LEVEL=DEBUG
   uv run --env-file .env.local python main.py
   ```

3. **Verify:**
   - Check logs for users found
   - Check logs for events processed
   - Verify email was sent (check Resend dashboard or inbox)
   - Check `email_digest_processed` table for processed events

4. **Test Edge Cases:**
   - User with no events → Should skip gracefully
   - User with events but no matching preferences → Should skip
   - User not a recipient → Should skip
   - Multiple projects → Should group correctly
   - Mentions → Should show mention count

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SUPABASE_URL` | Yes | - | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | - | Supabase service role key |
| `RESEND_API_KEY` | No* | - | Resend API key (*required to send emails) |
| `EMAIL_FROM` | No | `notifications@capmatch.com` | Sender email address |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `RESEND_TEST_MODE` | No | `true` | Enable test mode (uses test recipients) |
| `RESEND_TEST_RECIPIENT` | No | - | Override recipient in test mode |
| `RESEND_FORCE_TO_EMAIL` | No | - | Force all emails to this address |
| `SKIP_IDEMPOTENCY_CHECK` | No | `false` | Reprocess already-processed events |
| `DIGEST_TEMPLATE_PATH` | No | Auto-detected | Path to compiled HTML template |

## Troubleshooting

### No users found
- Check `user_notification_preferences` table
- Verify users have `status='digest'` and `channel='email'`
- Check Supabase connection and credentials

### No events found
- Verify `domain_events` table has events from last 24 hours
- Check timezone (worker uses UTC)
- Use `SKIP_IDEMPOTENCY_CHECK=true` to reprocess old events

### Email not sending
- Verify `RESEND_API_KEY` is set correctly
- Check Resend API dashboard for errors
- Use `RESEND_TEST_MODE=true` with sandbox recipients first
- Check `EMAIL_FROM` domain is verified in Resend

### Template not found
- Run `npm run render` in `packages/email-templates/`
- Check `DIGEST_TEMPLATE_PATH` environment variable
- Verify `dist/digest-template.html` exists

### Rate limiting
- Resend free tier: 2 requests/second
- Worker includes automatic throttling and retries
- Check logs for rate limit warnings

## Quick Test Commands

```bash
# Test email sending only (no DB)
uv run --env-file .env.local python scripts/send_resend_test.py --scenario delivered

# Test full worker locally
uv run --env-file .env.local python main.py

# Test with Docker
./run-email-digest.sh

# Preview templates
cd ../../packages/email-templates && npm run preview
```

