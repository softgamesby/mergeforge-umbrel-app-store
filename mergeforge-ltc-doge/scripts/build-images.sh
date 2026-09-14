#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "Building MergeForge web image..."
docker build --platform linux/amd64 -t mergeforge-web:0.1.0 web
echo "Building c2pool backend from upstream tag v0.2.0..."
docker build --platform linux/amd64 -t mergeforge-c2pool:0.1.0 c2pool
echo "Build complete. Validate with ./scripts/validate.sh"
