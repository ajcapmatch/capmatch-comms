-- Create a webhook trigger for public.domain_events table
-- This will send a POST request to your webhook URL whenever a new row is inserted

-- Replace 'http://your-webhook-url' with your actual webhook endpoint
create trigger "domain_events_webhook" 
after insert on "public"."domain_events" 
for each row
execute function "supabase_functions"."http_request"(
  'http://your-webhook-url',  -- Replace with your actual webhook URL
  'POST',
  '{"Content-Type":"application/json"}',
  '{}',
  '1000'  -- Timeout in milliseconds (1000ms = 1 second)
);

-- To drop the webhook trigger if needed:
-- DROP TRIGGER IF EXISTS "domain_events_webhook" ON "public"."domain_events";

