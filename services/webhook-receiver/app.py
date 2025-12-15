#!/usr/bin/env python3
"""
Webhook receiver server for Supabase database webhooks.
Use with ngrok to expose this server and receive webhook events.
"""

from flask import Flask, request, jsonify
from datetime import datetime
import json
import sys

# Force unbuffered output so logs appear immediately
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

app = Flask(__name__)

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_separator():
    """Print a visual separator line."""
    print(f"{Colors.OKCYAN}{'=' * 80}{Colors.ENDC}")


def print_event(event_data, headers=None):
    """Pretty print webhook event data."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print_separator()
    print(f"{Colors.BOLD}{Colors.OKGREEN}📨 Webhook Event Received{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Timestamp: {timestamp}{Colors.ENDC}")
    print_separator()
    
    if headers:
        print(f"\n{Colors.BOLD}Headers:{Colors.ENDC}")
        for key, value in headers.items():
            print(f"  {Colors.OKBLUE}{key}:{Colors.ENDC} {value}")
    
    print(f"\n{Colors.BOLD}Payload:{Colors.ENDC}")
    print(json.dumps(event_data, indent=2, default=str))
    print_separator()
    print()  # Empty line for readability
    sys.stdout.flush()  # Force flush to ensure output appears immediately


@app.route('/', methods=['GET', 'POST'])
def health_check():
    """Health check endpoint."""
    if request.method == 'POST':
        # Log POST requests to root endpoint (wrong endpoint)
        print(f"{Colors.WARNING}⚠️  POST request received at / (root) instead of /webhook{Colors.ENDC}")
        print(f"{Colors.WARNING}   Redirect your webhook to: http://localhost:{request.environ.get('SERVER_PORT', '5001')}/webhook{Colors.ENDC}")
        sys.stdout.flush()
        return jsonify({
            "status": "error",
            "message": "POST requests should go to /webhook, not /",
            "correct_endpoint": "/webhook"
        }), 405
    
    return jsonify({
        "status": "ok",
        "message": "Webhook receiver is running",
        "endpoints": {
            "webhook": "/webhook",
            "health": "/"
        }
    }), 200


@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    """Main webhook endpoint that receives Supabase database webhook events."""
    try:
        # Get headers
        headers = dict(request.headers)
        
        # Get request data
        if request.is_json:
            data = request.get_json()
        else:
            # Try to parse as JSON string if not already JSON
            try:
                data = json.loads(request.data.decode('utf-8'))
            except:
                data = {"raw_data": request.data.decode('utf-8')}
        
        # Print the event
        print_event(data, headers)
        
        # Return success response
        return jsonify({
            "status": "received",
            "message": "Webhook event logged successfully"
        }), 200
        
    except Exception as e:
        error_msg = f"Error processing webhook: {str(e)}"
        print(f"{Colors.FAIL}❌ {error_msg}{Colors.ENDC}", file=sys.stderr)
        sys.stderr.flush()
        return jsonify({
            "status": "error",
            "message": error_msg
        }), 500


@app.route('/webhook', methods=['GET'])
def webhook_get():
    """Handle GET requests to webhook endpoint (for testing)."""
    return jsonify({
        "status": "ok",
        "message": "Webhook endpoint is ready. Send POST requests here.",
        "method": "POST",
        "url": "/webhook"
    }), 200


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    
    print(f"{Colors.BOLD}{Colors.OKGREEN}")
    print("=" * 80)
    print("🚀 Webhook Receiver Server Starting")
    print("=" * 80)
    print(f"{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Server running on: http://localhost:{port}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Webhook endpoint: http://localhost:{port}/webhook{Colors.ENDC}")
    print(f"{Colors.WARNING}")
    print("To expose with ngrok, run:")
    print(f"  ngrok http {port}")
    print(f"{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKGREEN}{'=' * 80}{Colors.ENDC}\n")
    sys.stdout.flush()
    
    # Disable Flask's default request logging to avoid clutter
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    app.run(host='0.0.0.0', port=port, debug=False)

