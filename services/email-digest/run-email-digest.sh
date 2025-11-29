#!/usr/bin/env bash
# Email digest worker runner script
# Usage: ./run-email-digest.sh
#
# This script runs the email digest worker in a Docker container.
# Ensure you have:
# - Docker installed and your user in the docker group
# - .env file in this directory with required environment variables
# - Docker image built: docker build -t capmatch-email-digest:prod .

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default log file (can be overridden via EMAIL_DIGEST_LOG env var)
LOG_FILE="${EMAIL_DIGEST_LOG:-/var/log/email-digest.log}"

# Ensure log file exists and is writable
if [ ! -f "$LOG_FILE" ]; then
    touch "$LOG_FILE" 2>/dev/null || {
        echo "Warning: Cannot create log file at $LOG_FILE. Logging to stdout instead."
        LOG_FILE="/dev/stdout"
    }
fi

# Run the Docker container
/usr/bin/docker run --rm \
    --env-file .env \
    capmatch-email-digest:prod >> "$LOG_FILE" 2>&1

