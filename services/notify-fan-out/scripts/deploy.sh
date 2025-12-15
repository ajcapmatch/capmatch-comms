#!/usr/bin/env bash
# Deployment script for notify-fan-out service
# Deploys to Google Cloud Run
# Usage: ./scripts/deploy.sh [PROJECT_ID] [REGION]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$SERVICE_ROOT/../.." && pwd)"

# Default values
PROJECT_ID="${1:-${GCP_PROJECT_ID}}"
REGION="${2:-us-west1}"
SERVICE_NAME="notify-fan-out"
IMAGE_NAME="us-central1-docker.pkg.dev/${PROJECT_ID}/${SERVICE_NAME}/${SERVICE_NAME}"

echo "=========================================="
echo "Notify Fan-Out Service - Cloud Run Deploy"
echo "=========================================="

if [ -z "$PROJECT_ID" ]; then
    echo "ERROR: PROJECT_ID is required"
    echo "Usage: ./scripts/deploy.sh <PROJECT_ID> [REGION]"
    echo "  or set GCP_PROJECT_ID environment variable"
    exit 1
fi

echo ""
echo "Configuration:"
echo "  Project:  $PROJECT_ID"
echo "  Region:   $REGION"
echo "  Service:  $SERVICE_NAME"
echo "  Image:    $IMAGE_NAME"
echo ""

# Ensure we're authenticated
echo "Checking GCP authentication..."
gcloud auth print-access-token > /dev/null 2>&1 || {
    echo "ERROR: Not authenticated with GCP. Run: gcloud auth login"
    exit 1
}

# Set project
gcloud config set project "$PROJECT_ID"

# Create artifact registry repo if not exists
echo "Ensuring artifact registry repository exists..."
gcloud artifacts repositories describe "$SERVICE_NAME" \
    --location=us-central1 \
    --project="$PROJECT_ID" > /dev/null 2>&1 || \
gcloud artifacts repositories create "$SERVICE_NAME" \
    --repository-format=docker \
    --location=us-central1 \
    --project="$PROJECT_ID"

# Build and push image
echo ""
echo "Building and pushing Docker image..."
cd "$REPO_ROOT"

COMMIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "latest")
FULL_IMAGE="${IMAGE_NAME}:${COMMIT_SHA}"

docker build -f "services/notify-fan-out/Dockerfile" -t "$FULL_IMAGE" .
docker tag "$FULL_IMAGE" "${IMAGE_NAME}:latest"

# Configure docker for artifact registry
gcloud auth configure-docker us-central1-docker.pkg.dev --quiet

docker push "$FULL_IMAGE"
docker push "${IMAGE_NAME}:latest"

# Deploy to Cloud Run
echo ""
echo "Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --image "$FULL_IMAGE" \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --timeout 30s \
    --concurrency 80

# Get service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --format "value(status.url)")

echo ""
echo "=========================================="
echo "Deployment complete!"
echo "=========================================="
echo ""
echo "Service URL: $SERVICE_URL"
echo "Webhook URL: ${SERVICE_URL}/webhook"
echo ""
echo "To set environment variables:"
echo "  gcloud run services update $SERVICE_NAME \\"
echo "    --region $REGION \\"
echo "    --set-env-vars SUPABASE_URL=<url>,SUPABASE_SERVICE_ROLE_KEY=<key>"
echo ""

