#!/bin/bash
# Run the webhook receiver server

PORT=${1:-5000}

echo "Starting webhook receiver on port $PORT..."
python3 app.py $PORT

