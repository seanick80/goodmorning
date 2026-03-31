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
# IMPORTANT: Deploys NEVER modify database contents. Migrations (schema changes)
# run automatically, but user data (widget config, cached API data) is preserved.
# To seed a fresh DB with defaults, run manually on the Pi:
#   sudo -u goodmorning bash -c 'cd /opt/goodmorning/backend && source .venv/bin/activate && python manage.py seed_data'
#
# Supports two sync methods:
#   - rsync (preferred) — fast incremental sync with --delete for clean deploys
#   - scp+tar (fallback) — used when rsync is unavailable (e.g. Git Bash on Windows)
#     Uses atomic swap for backend to preserve .venv, .env, and logs

set -euo pipefail

PI_HOST="goodmorning.local"
PI_USER="pi"
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
# Check sync method
# -------------------------------------------------------------------
USE_RSYNC=false
if command -v rsync &>/dev/null; then
    USE_RSYNC=true
    info "Using rsync for file sync."
else
    info "rsync not found — using scp+tar fallback."
fi

# -------------------------------------------------------------------
# Build frontend
# -------------------------------------------------------------------
info "Building frontend..."
cd "$FRONTEND_DIR"
npm run build
cd "$ROOT_DIR"
ok "Frontend built."

# -------------------------------------------------------------------
# Sync functions
# -------------------------------------------------------------------
sync_with_rsync() {
    local RSYNC_OPTS="-az --delete --exclude=__pycache__ --exclude=*.pyc --exclude=.venv --exclude=logs --exclude=.env --exclude=staticfiles"

    if [[ "$MODE" == "--frontend-only" ]]; then
        info "Syncing frontend only..."
        rsync $RSYNC_OPTS "$FRONTEND_DIR/dist/" "$PI_USER@$PI_HOST:$PI_DIR/frontend/dist/"
        ok "Frontend synced."
        return
    fi

    info "Syncing backend..."
    rsync $RSYNC_OPTS "$BACKEND_DIR/" "$PI_USER@$PI_HOST:$PI_DIR/backend/"

    info "Syncing frontend..."
    rsync $RSYNC_OPTS "$FRONTEND_DIR/dist/" "$PI_USER@$PI_HOST:$PI_DIR/frontend/dist/"

    info "Syncing Pi configs..."
    rsync $RSYNC_OPTS "$PI_CONF_DIR/" "$PI_USER@$PI_HOST:$PI_DIR/pi/"

    ok "Files synced."
}

sync_with_scp() {
    local TMPDIR="/tmp/goodmorning-deploy"

    if [[ "$MODE" == "--frontend-only" ]]; then
        info "Deploying frontend only..."
        tar czf /tmp/gm-frontend.tar.gz -C "$FRONTEND_DIR" dist/
        scp /tmp/gm-frontend.tar.gz "$PI_USER@$PI_HOST:/tmp/"
        ssh "$PI_USER@$PI_HOST" "\
            sudo rm -rf $PI_DIR/frontend/dist && \
            sudo mkdir -p $PI_DIR/frontend/dist && \
            sudo tar xzf /tmp/gm-frontend.tar.gz -C $PI_DIR/frontend/ && \
            sudo chown -R goodmorning:goodmorning $PI_DIR/frontend && \
            rm /tmp/gm-frontend.tar.gz"
        ok "Frontend synced."
        return
    fi

    # --- Backend: atomic swap preserving .venv, .env, logs ---
    info "Packaging backend..."
    tar czf /tmp/gm-backend.tar.gz \
        --exclude=__pycache__ --exclude='*.pyc' \
        --exclude=.venv --exclude=logs \
        --exclude=db.sqlite3 --exclude=staticfiles \
        --exclude=.env \
        -C "$ROOT_DIR" backend/

    info "Packaging frontend..."
    tar czf /tmp/gm-frontend.tar.gz -C "$FRONTEND_DIR" dist/

    info "Uploading to Pi..."
    scp /tmp/gm-backend.tar.gz /tmp/gm-frontend.tar.gz "$PI_USER@$PI_HOST:/tmp/"

    info "Deploying backend (atomic swap)..."
    ssh "$PI_USER@$PI_HOST" "\
        sudo rm -rf $TMPDIR && \
        sudo mkdir -p $TMPDIR/backend && \
        sudo tar xzf /tmp/gm-backend.tar.gz -C $TMPDIR/backend --strip-components=1 && \
        for f in manage.py config/settings.py dashboard/views.py; do \
            if [ ! -f $TMPDIR/backend/\$f ]; then \
                echo \"DEPLOY ABORT: missing $TMPDIR/backend/\$f after extraction\" >&2; \
                exit 1; \
            fi; \
        done && \
        sudo cp -a $PI_DIR/backend/.venv $TMPDIR/backend/.venv && \
        sudo cp -a $PI_DIR/backend/.env  $TMPDIR/backend/.env && \
        sudo cp -a $PI_DIR/backend/logs  $TMPDIR/backend/logs 2>/dev/null; \
        sudo rm -rf $PI_DIR/backend_old && \
        sudo mv $PI_DIR/backend $PI_DIR/backend_old && \
        sudo mv $TMPDIR/backend $PI_DIR/backend && \
        sudo chown -R goodmorning:goodmorning $PI_DIR/backend && \
        sudo rm -rf $PI_DIR/backend_old $TMPDIR"
    ok "Backend deployed."

    info "Deploying frontend (clean install)..."
    ssh "$PI_USER@$PI_HOST" "\
        sudo rm -rf $PI_DIR/frontend/dist && \
        sudo mkdir -p $PI_DIR/frontend/dist && \
        sudo tar xzf /tmp/gm-frontend.tar.gz -C $PI_DIR/frontend/ && \
        sudo chown -R goodmorning:goodmorning $PI_DIR/frontend"
    ok "Frontend deployed."

    # --- Pi configs ---
    if [[ -d "$PI_CONF_DIR" ]]; then
        info "Syncing Pi configs..."
        tar czf /tmp/gm-pi.tar.gz -C "$ROOT_DIR" pi/
        scp /tmp/gm-pi.tar.gz "$PI_USER@$PI_HOST:/tmp/"
        ssh "$PI_USER@$PI_HOST" "\
            sudo rm -rf $PI_DIR/pi && \
            sudo mkdir -p $PI_DIR/pi && \
            sudo tar xzf /tmp/gm-pi.tar.gz -C $PI_DIR --strip-components=0 && \
            sudo chown -R goodmorning:goodmorning $PI_DIR/pi && \
            rm /tmp/gm-pi.tar.gz"
        ok "Pi configs synced."
    fi

    # Clean up temp files
    ssh "$PI_USER@$PI_HOST" "rm -f /tmp/gm-backend.tar.gz /tmp/gm-frontend.tar.gz"
    rm -f /tmp/gm-backend.tar.gz /tmp/gm-frontend.tar.gz /tmp/gm-pi.tar.gz
    ok "Files synced."
}

# -------------------------------------------------------------------
# Run sync
# -------------------------------------------------------------------
if $USE_RSYNC; then
    sync_with_rsync
else
    sync_with_scp
fi

# Frontend-only exits early from sync functions
if [[ "$MODE" == "--frontend-only" ]]; then
    info "Reloading nginx..."
    ssh "$PI_USER@$PI_HOST" "sudo systemctl reload nginx"
    ok "Done."
    exit 0
fi

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

# -------------------------------------------------------------------
# Post-deploy verification
# -------------------------------------------------------------------
info "Verifying deploy..."
VERIFY_RESULT=$(ssh "$PI_USER@$PI_HOST" "\
    STATUS=0; \
    for f in manage.py config/settings.py dashboard/views.py dashboard/jobs.py; do \
        if [ ! -f $PI_DIR/backend/\$f ]; then \
            echo \"MISSING: $PI_DIR/backend/\$f\"; STATUS=1; \
        fi; \
    done; \
    if [ ! -d $PI_DIR/frontend/dist ]; then \
        echo 'MISSING: frontend/dist/'; STATUS=1; \
    fi; \
    if ! curl -sf -o /dev/null http://127.0.0.1:8000/api/dashboard/; then \
        echo 'FAIL: API not responding'; STATUS=1; \
    fi; \
    exit \$STATUS" 2>&1) || {
    fail "Post-deploy verification FAILED:\n$VERIFY_RESULT"
}
ok "Deploy verified — all files present, API responding."
ok "Deploy complete."
