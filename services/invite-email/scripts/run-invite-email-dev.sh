#!/usr/bin/env bash
# Invite email worker development runner script (foreground mode with logs)
# Usage: ./scripts/run-invite-email-dev.sh
#
# This script runs the invite email worker in foreground mode so you can:
# - See logs in real-time
# - Stop it with Ctrl+C
# Ensure you have:
# - Docker installed and your user in the docker group
# - .env file in the service root directory with required environment variables
# - Docker image built: docker build -f services/invite-email/Dockerfile -t capmatch-invite-email:prod .

set -e

# Get the directory where this script is located (scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Get the service root directory (parent of scripts/)
SERVICE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SERVICE_ROOT"

# Run the Docker container
DOCKER_BIN="$(command -v docker || true)"
if [ -z "$DOCKER_BIN" ]; then
    echo "Error: docker binary not found in PATH."
    exit 1
fi

# Check if container exists (running or stopped)
CONTAINER_NAME="capmatch-invite-email"
if "$DOCKER_BIN" ps -aq -f name="$CONTAINER_NAME" | grep -q .; then
    if "$DOCKER_BIN" ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        echo "Warning: Container $CONTAINER_NAME is already running."
        echo "Stop it first: docker stop $CONTAINER_NAME"
        exit 1
    else
        echo "Removing stopped container $CONTAINER_NAME..."
        "$DOCKER_BIN" rm "$CONTAINER_NAME" > /dev/null 2>&1 || true
    fi
fi

echo "Starting invite email worker in foreground mode..."
echo "Press Ctrl+C to stop"
echo ""

# Run in foreground (no -d flag) so logs are visible and Ctrl+C works
"$DOCKER_BIN" run --rm \
    --name "$CONTAINER_NAME" \
    --env-file "$SERVICE_ROOT/.env" \
    capmatch-invite-email:prod

