#!/usr/bin/env bash
# pi-update.sh — Run on the Pi after rsync to apply updates.
# Called by deploy-pi.sh over SSH; can also be run manually.
#
# Usage:
#   /opt/goodmorning/pi/pi-update.sh           # Quick: migrate + restart
#   /opt/goodmorning/pi/pi-update.sh --full    # Full: install deps + migrate + restart
#   /opt/goodmorning/pi/pi-update.sh --setup   # Re-install systemd/nginx configs

set -euo pipefail

APP_DIR="/opt/goodmorning"
BACKEND="$APP_DIR/backend"
VENV="$BACKEND/.venv"
PIP="$VENV/bin/pip"
PYTHON="$VENV/bin/python"
MODE="${1:-quick}"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

info() { echo -e "${CYAN}[pi]${NC} $*"; }
ok()   { echo -e "${GREEN}[pi]${NC} $*"; }

# Load configuration
CONF_FILE="$APP_DIR/pi/pi.conf"
if [[ -f "$CONF_FILE" ]]; then
    # shellcheck source=pi.conf
    source "$CONF_FILE"
fi
GM_DATABASE="${GM_DATABASE:-postgres}"

# Create venv if missing
if [[ ! -d "$VENV" ]]; then
    info "Creating Python virtual environment..."
    python3 -m venv "$VENV"
    MODE="--full"
fi

# Ensure venv ownership is correct (atomic swap deploys can leave root-owned files)
info "Fixing venv ownership..."
sudo chown -R goodmorning:goodmorning "$BACKEND"

# Full mode: install/upgrade dependencies
if [[ "$MODE" == "--full" || "$MODE" == "--setup" ]]; then
    info "Installing Python dependencies..."
    $PIP install -q --upgrade pip
    $PIP install -q -r "$BACKEND/requirements.txt"
fi

# Run migrations
info "Running database migrations..."
$PYTHON "$BACKEND/manage.py" migrate --no-input

# Collect static files (Django admin CSS/JS)
info "Collecting static files..."
$PYTHON "$BACKEND/manage.py" collectstatic --no-input --clear -v0

# Re-install configs if --setup
if [[ "$MODE" == "--setup" ]]; then
    info "Re-running pi-setup.sh for config installation..."
    sudo bash "$APP_DIR/pi/pi-setup.sh"
    exit 0
fi

# Restart application services
info "Restarting services..."
sudo systemctl restart goodmorning-web goodmorning-scheduler

# Health check — wait for gunicorn to come up
info "Waiting for API..."
for i in $(seq 1 15); do
    if curl -sf http://localhost:8000/api/weather/ > /dev/null 2>&1; then
        ok "API is responding."
        break
    fi
    sleep 1
    if [[ $i -eq 15 ]]; then
        echo "WARNING: API did not respond within 15 seconds."
    fi
done

ok "Update complete."
