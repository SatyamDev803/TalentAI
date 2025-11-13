#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Navigate to the job service directory
# From: backend/scripts/services/job/
# To: backend/services/job_service/
cd "$SCRIPT_DIR/../../../services/resume_parser_service" || exit 1

echo "Starting Resume Parser Service on port 8003..."
echo "Working directory: $(pwd)"
echo "Adding shared modules to PYTHONPATH..."
echo ""

# Set PYTHONPATH to include shared modules
export PYTHONPATH="../../shared:$PYTHONPATH"

# Start the service
poetry run uvicorn app.main:app \
    --reload \
    --host 0.0.0.0 \
    --port 8003
