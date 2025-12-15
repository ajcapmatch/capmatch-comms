# Webhook Receiver Server

A simple Flask server to receive and log Supabase database webhook events.

## Setup

1. Install dependencies:
```bash
cd services/webhook-receiver
pip install flask
# or if using uv:
uv pip install flask
```

## Usage

### Start the server:
```bash
python app.py
# or specify a custom port:
python app.py 8080
```

The server will start on `http://localhost:5000` (or your specified port).

### Expose with ngrok:

1. Install ngrok if you haven't already: https://ngrok.com/download

2. In a new terminal, run:
```bash
ngrok http 5000
```

3. Copy the HTTPS URL from ngrok (e.g., `https://abc123.ngrok-free.app`)

4. Update your Supabase webhook SQL to use this URL:
```sql
create trigger "domain_events_webhook" 
after insert on "public"."domain_events" 
for each row
execute function "supabase_functions"."http_request"(
  'https://abc123.ngrok-free.app/webhook',  -- Your ngrok URL + /webhook
  'POST',
  '{"Content-Type":"application/json"}',
  '{}',
  '1000'
);
```

## Endpoints

- `GET /` - Health check
- `POST /webhook` - Main webhook endpoint (receives Supabase events)
- `GET /webhook` - Test endpoint to verify it's working

## Output

The server will print formatted webhook events to your terminal with:
- Timestamp
- Headers
- Full payload (pretty-printed JSON)

Events are color-coded for easy reading in the terminal.

