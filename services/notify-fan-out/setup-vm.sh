#!/usr/bin/env bash
# VM Setup Script for Notify Fan-Out Service
# This script sets up the notify-fan-out service on a GCP VM (one-time setup)
# Usage: ./setup-vm.sh

set -e

echo "=========================================="
echo "Notify Fan-Out Service - VM Setup"
echo "=========================================="

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Locate repo root (where .git lives) for Docker build context
REPO_ROOT="$SCRIPT_DIR"
while [ "$REPO_ROOT" != "/" ] && [ ! -d "$REPO_ROOT/.git" ]; do
    REPO_ROOT="$(dirname "$REPO_ROOT")"
done

HAS_GIT_ROOT=false
if [ -d "$REPO_ROOT/.git" ]; then
    HAS_GIT_ROOT=true
else
    REPO_ROOT="$SCRIPT_DIR"
fi

# Check if running as root (we'll use sudo where needed)
if [ "$EUID" -eq 0 ]; then 
   echo "Please don't run this script as root. It will use sudo when needed."
   exit 1
fi

echo ""
echo "Step 1: Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y git

echo ""
echo "Step 2: Checking Docker installation..."
if command -v docker > /dev/null 2>&1 && docker info > /dev/null 2>&1; then
    echo "✓ Docker is already installed and working"
elif command -v docker > /dev/null 2>&1; then
    echo "⚠️  Docker command exists but daemon is not accessible"
    echo "   You may need to log out and back in, or run: newgrp docker"
else
    echo "Installing Docker..."
    # Try to install docker.io, but handle conflicts gracefully
    if ! sudo apt-get install -y docker.io 2>&1; then
        echo "⚠️  Docker installation had issues (may be conflict with existing Docker)"
        echo "   If Docker is already installed via another method, continuing..."
    fi
fi

echo ""
echo "Step 3: Setting up Docker group..."
if ! groups | grep -q docker; then
    sudo usermod -aG docker "$USER"
    echo "✓ Added user to docker group. You may need to log out and back in for group changes to take effect."
    NEED_LOGOUT=true
else
    echo "✓ User is already in docker group"
    NEED_LOGOUT=false
fi

echo ""
echo "Step 4: Setting timezone to Pacific Time..."
sudo timedatectl set-timezone America/Los_Angeles
echo "✓ Timezone set to America/Los_Angeles"

echo ""
echo "Step 5: Creating log directory..."
sudo mkdir -p /var/log
sudo touch /var/log/notify-fan-out.log
sudo chown "$USER:$USER" /var/log/notify-fan-out.log
echo "✓ Log file created at /var/log/notify-fan-out.log"

echo ""
echo "Step 6: Building Docker image..."
if docker info > /dev/null 2>&1; then
    if [ "$HAS_GIT_ROOT" = true ]; then
        docker build -f "$REPO_ROOT/services/notify-fan-out/Dockerfile" -t capmatch-notify-fan-out:prod "$REPO_ROOT"
    else
        docker build -f "$SCRIPT_DIR/Dockerfile" -t capmatch-notify-fan-out:prod "$SCRIPT_DIR"
    fi
    echo "✓ Docker image built successfully"
else
    echo "⚠️  Docker daemon not accessible. Skipping image build."
    echo "   After logging out and back in (or running 'newgrp docker'), run:"
    if [ "$HAS_GIT_ROOT" = true ]; then
        echo "   docker build -f $REPO_ROOT/services/notify-fan-out/Dockerfile -t capmatch-notify-fan-out:prod $REPO_ROOT"
    else
        echo "   docker build -f $SCRIPT_DIR/Dockerfile -t capmatch-notify-fan-out:prod $SCRIPT_DIR"
    fi
    SKIP_BUILD=true
fi

echo ""
echo "Step 7: Setting up cron job..."
CRON_CMD="* * * * * $SCRIPT_DIR/run-notify-fan-out.sh"
(crontab -l 2>/dev/null | grep -v "run-notify-fan-out.sh"; echo "$CRON_CMD") | crontab -
echo "✓ Cron job added (runs every minute)"

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Ensure .env file exists in this directory with required variables:"
echo "   - SUPABASE_URL"
echo "   - SUPABASE_SERVICE_ROLE_KEY"
echo ""
if [ "$NEED_LOGOUT" = "true" ] || [ "${SKIP_BUILD:-false}" = "true" ]; then
    echo "2. Log out and back in (or run 'newgrp docker') to pick up docker group changes"
    if [ "${SKIP_BUILD:-false}" = "true" ]; then
        echo "   Then build the Docker image manually (see command above)"
    fi
    echo ""
    echo "3. Test the service manually:"
    echo "   ./run-notify-fan-out.sh"
else
    echo "2. Test the service manually:"
    echo "   ./run-notify-fan-out.sh"
fi
echo ""
echo "4. Check logs:"
echo "   tail -f /var/log/notify-fan-out.log"
echo ""
echo "5. View cron schedule:"
echo "   crontab -l"
echo ""

