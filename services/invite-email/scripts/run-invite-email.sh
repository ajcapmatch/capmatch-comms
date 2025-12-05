#!/usr/bin/env bash
# Invite email worker daemon runner script
# Usage: ./scripts/run-invite-email.sh
#
# This script runs the invite email worker as a daemon Docker container.
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

# Default log file (can be overridden via INVITE_EMAIL_LOG env var)
LOG_FILE="${INVITE_EMAIL_LOG:-/var/log/invite-email.log}"

# Ensure log file exists and is writable
if [ ! -f "$LOG_FILE" ]; then
    touch "$LOG_FILE" 2>/dev/null || {
        echo "Warning: Cannot create log file at $LOG_FILE. Logging to stdout instead."
        LOG_FILE="/dev/stdout"
    }
fi

# Run the Docker container
DOCKER_BIN="$(command -v docker || true)"
if [ -z "$DOCKER_BIN" ]; then
    echo "Error: docker binary not found in PATH."
    exit 1
fi

# Check if container is already running
CONTAINER_NAME="capmatch-invite-email"
if "$DOCKER_BIN" ps -q -f name="$CONTAINER_NAME" | grep -q .; then
    echo "Warning: Container $CONTAINER_NAME is already running."
    echo "To stop it: docker stop $CONTAINER_NAME"
    echo "To view logs: docker logs -f $CONTAINER_NAME"
    exit 1
fi

# Run as daemon with auto-restart
"$DOCKER_BIN" run -d \
    --name "$CONTAINER_NAME" \
    --restart=unless-stopped \
    --env-file "$SERVICE_ROOT/.env" \
    capmatch-invite-email:prod >> "$LOG_FILE" 2>&1

echo "Invite email worker daemon started."
echo "Container name: $CONTAINER_NAME"
echo "To view logs: docker logs -f $CONTAINER_NAME"
echo "To stop: docker stop $CONTAINER_NAME"
echo "To restart: docker restart $CONTAINER_NAME"

