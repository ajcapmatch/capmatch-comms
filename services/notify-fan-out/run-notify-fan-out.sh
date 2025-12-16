#!/usr/bin/env bash
# Notify Fan-Out service runner script
# Usage: ./run-notify-fan-out.sh
#
# This script runs the notify-fan-out service in a Docker container.
# Ensure you have:
# - Docker installed and your user in the docker group
# - .env file in this directory with required environment variables
# - Docker image built: docker build -f services/notify-fan-out/Dockerfile -t capmatch-notify-fan-out:prod .

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default log file (can be overridden via NOTIFY_FAN_OUT_LOG env var)
LOG_FILE="${NOTIFY_FAN_OUT_LOG:-/var/log/notify-fan-out.log}"

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

"$DOCKER_BIN" run --rm \
    --env-file .env \
    capmatch-notify-fan-out:prod >> "$LOG_FILE" 2>&1

