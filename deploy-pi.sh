#!/usr/bin/env bash
# deploy-pi.sh — Push updates from dev machine to Raspberry Pi.
#
# Usage:
#   ./deploy-pi.sh                    Update code + restart (default)
#   ./deploy-pi.sh --full             Full: rebuild deps + migrate + restart
#   ./deploy-pi.sh --frontend-only    Rebuild and push frontend only
#   ./deploy-pi.sh --restart          Just restart services on Pi
#   ./deploy-pi.sh --setup            First deploy: push everything + install configs
#   ./deploy-pi.sh --status           Show Pi health check
#
# Prerequisites: SSH key auth to goodmorning.local

set -euo pipefail

PI_HOST="goodmorning.local"
PI_USER="goodmorning"
PI_DIR="/opt/goodmorning"
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
PI_CONF_DIR="$ROOT_DIR/pi"

CYAN='\033[0;36m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

info() { echo -e "${CYAN}[deploy]${NC} $*"; }
ok()   { echo -e "${GREEN}[deploy]${NC} $*"; }
fail() { echo -e "${RED}[deploy]${NC} $*"; exit 1; }

MODE="${1:-default}"

# -------------------------------------------------------------------
# Status check (no deploy)
# -------------------------------------------------------------------
if [[ "$MODE" == "--status" ]]; then
    ssh "$PI_USER@$PI_HOST" "$PI_DIR/pi/pi-health.sh"
    exit 0
fi

# -------------------------------------------------------------------
# Restart only (no deploy)
# -------------------------------------------------------------------
if [[ "$MODE" == "--restart" ]]; then
    info "Restarting services on Pi..."
    ssh "$PI_USER@$PI_HOST" "sudo systemctl restart goodmorning-web goodmorning-scheduler"
    ok "Services restarted."
    exit 0
fi

# -------------------------------------------------------------------
# Verify SSH connectivity
# -------------------------------------------------------------------
info "Checking SSH connectivity to $PI_HOST..."
if ! ssh -o ConnectTimeout=5 "$PI_USER@$PI_HOST" true 2>/dev/null; then
    fail "Cannot reach $PI_USER@$PI_HOST via SSH. Is the Pi on the network?"
fi
ok "SSH connected."

# -------------------------------------------------------------------
# Build frontend
# -------------------------------------------------------------------
info "Building frontend..."
cd "$FRONTEND_DIR"
npm run build
cd "$ROOT_DIR"
ok "Frontend built."

# -------------------------------------------------------------------
# Rsync files to Pi
# -------------------------------------------------------------------
RSYNC_OPTS="-az --delete --exclude=__pycache__ --exclude=*.pyc --exclude=.venv --exclude=logs --exclude=.env"

if [[ "$MODE" == "--frontend-only" ]]; then
    info "Syncing frontend only..."
    rsync $RSYNC_OPTS "$FRONTEND_DIR/dist/" "$PI_USER@$PI_HOST:$PI_DIR/frontend/dist/"
    ok "Frontend synced."

    info "Restarting nginx..."
    ssh "$PI_USER@$PI_HOST" "sudo systemctl reload nginx"
    ok "Done."
    exit 0
fi

info "Syncing backend..."
rsync $RSYNC_OPTS \
    --exclude=staticfiles \
    "$BACKEND_DIR/" "$PI_USER@$PI_HOST:$PI_DIR/backend/"

info "Syncing frontend..."
rsync $RSYNC_OPTS "$FRONTEND_DIR/dist/" "$PI_USER@$PI_HOST:$PI_DIR/frontend/dist/"

info "Syncing Pi configs..."
rsync $RSYNC_OPTS "$PI_CONF_DIR/" "$PI_USER@$PI_HOST:$PI_DIR/pi/"

ok "Files synced."

# -------------------------------------------------------------------
# Run update on Pi
# -------------------------------------------------------------------
case "$MODE" in
    --setup)
        info "Running first-time setup on Pi..."
        ssh "$PI_USER@$PI_HOST" "chmod +x $PI_DIR/pi/pi-update.sh $PI_DIR/pi/pi-health.sh && $PI_DIR/pi/pi-update.sh --setup"
        ;;
    --full)
        info "Running full update on Pi..."
        ssh "$PI_USER@$PI_HOST" "$PI_DIR/pi/pi-update.sh --full"
        ;;
    *)
        info "Running quick update on Pi..."
        ssh "$PI_USER@$PI_HOST" "$PI_DIR/pi/pi-update.sh"
        ;;
esac

ok "Deploy complete."
