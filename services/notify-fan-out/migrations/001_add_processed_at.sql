-- Migration: Add processed_at column to domain_events
-- This column tracks when each event was processed by notify-fan-out
-- Run this migration before deploying the polling-based service

-- 1. Add the processed_at column
ALTER TABLE public.domain_events 
ADD COLUMN IF NOT EXISTS processed_at TIMESTAMPTZ DEFAULT NULL;

-- 2. Create partial index for efficient querying of unprocessed events
CREATE INDEX IF NOT EXISTS idx_domain_events_unprocessed 
ON public.domain_events (id) 
WHERE processed_at IS NULL;

-- 3. Drop the webhook trigger (no longer needed with polling)
DROP TRIGGER IF EXISTS "domain_events_webhook" ON "public"."domain_events";

-- 4. Drop the helper function if it exists
DROP FUNCTION IF EXISTS public.notify_fan_out_http_trigger();

-- Optional: Mark all existing events as processed to avoid reprocessing
-- Uncomment if you don't want to reprocess historical events:
-- UPDATE public.domain_events SET processed_at = NOW() WHERE processed_at IS NULL;

