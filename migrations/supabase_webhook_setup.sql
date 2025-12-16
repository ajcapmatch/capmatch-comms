-- NOTE: The notify-fan-out service now uses polling instead of webhooks.
-- This file is kept for reference. See services/notify-fan-out/migrations/ for the new approach.

-- ============================================================================
-- MIGRATION: Add processed_at column for polling-based notify-fan-out
-- ============================================================================

-- 1. Add the processed_at column to track which events have been processed
ALTER TABLE public.domain_events 
ADD COLUMN IF NOT EXISTS processed_at TIMESTAMPTZ DEFAULT NULL;

-- 2. Create partial index for efficient querying of unprocessed events
CREATE INDEX IF NOT EXISTS idx_domain_events_unprocessed 
ON public.domain_events (id) 
WHERE processed_at IS NULL;

-- 3. Drop any existing webhook triggers (no longer needed with polling)
DROP TRIGGER IF EXISTS "domain_events_webhook" ON "public"."domain_events";
DROP FUNCTION IF EXISTS public.notify_fan_out_http_trigger();

-- ============================================================================
-- LEGACY: Webhook trigger (for reference only - DO NOT USE)
-- ============================================================================
-- The following was used for the webhook-based approach, now replaced by polling:
--
-- create trigger "domain_events_webhook" 
-- after insert on "public"."domain_events" 
-- for each row
-- execute function "supabase_functions"."http_request"(
--   'http://your-webhook-url',  -- Replace with your actual webhook URL
--   'POST',
--   '{"Content-Type":"application/json"}',
--   '{}',
--   '1000'  -- Timeout in milliseconds (1000ms = 1 second)
-- );
