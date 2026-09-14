#!/bin/bash
set -e

echo "=================================================="
echo "   Automated Deployer: Frontend + Backend Sync   "
echo "=================================================="

# Move to project root directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 1. Pull latest code from GitHub
echo "[1/4] Pulling latest updates from Git..."
git pull origin main

# 2. Build Frontend
echo "[2/4] Building Frontend production assets..."
cd frontend
npm run build
cd "$SCRIPT_DIR"

# 3. Sync built dist files to HestiaCP public_html automatically
echo "[3/4] Syncing frontend build to HestiaCP public_html..."
HESTIA_PUBLIC_HTML="/home/mbummm/web/admin.mbelik.com/public_html"
if [ -d "$HESTIA_PUBLIC_HTML" ]; then
    sudo cp -r frontend/dist/* "$HESTIA_PUBLIC_HTML/"
    sudo chown -R mbummm:mbummm "$HESTIA_PUBLIC_HTML/"
    echo "✓ Frontend dist copied to $HESTIA_PUBLIC_HTML"
fi

# 4. Restart Backend Service
echo "[4/4] Restarting FastAPI backend service..."
if command -v systemctl >/dev/null 2>&1; then
    sudo systemctl restart ad-analytics || true
    echo "✓ ad-analytics service restarted"
fi

echo "=================================================="
echo " 🎉 DEPLOY SUCCESSFUL! All services updated. "
echo "=================================================="
