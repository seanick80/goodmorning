#!/usr/bin/env bash
# pi-setup.sh — One-time bootstrap for Raspberry Pi 5.
#
# Run this on the Pi after first boot:
#   ssh goodmorning.local 'bash -s' < pi/pi-setup.sh
#
# Or copy it to the Pi and run:
#   sudo bash /opt/goodmorning/pi/pi-setup.sh
#
# Configuration is read from pi/pi.conf. Edit that file before running.
#
# Prerequisites: Raspberry Pi OS (64-bit), SSH enabled, Wi-Fi configured.

set -euo pipefail

APP_DIR="/opt/goodmorning"
APP_USER="goodmorning"
PI_HOME="/home/pi"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${CYAN}[setup]${NC} $*"; }
ok()   { echo -e "${GREEN}[setup]${NC} $*"; }
warn() { echo -e "${YELLOW}[setup]${NC} $*"; }
fail() { echo -e "${RED}[setup]${NC} $*"; exit 1; }

# Must run as root
if [[ $EUID -ne 0 ]]; then
    fail "This script must be run as root (use sudo)."
fi

# -------------------------------------------------------------------
# 0. Load configuration
# -------------------------------------------------------------------
CONF_FILE="$APP_DIR/pi/pi.conf"
if [[ -f "$CONF_FILE" ]]; then
    # shellcheck source=pi.conf
    source "$CONF_FILE"
    ok "Loaded configuration from pi.conf"
else
    warn "pi.conf not found — using defaults (postgres, 2 workers, full desktop, vnc on)"
fi

GM_DATABASE="${GM_DATABASE:-postgres}"
GM_WORKERS="${GM_WORKERS:-2}"
GM_DESKTOP="${GM_DESKTOP:-full}"
GM_VNC="${GM_VNC:-on}"

info "Configuration: database=$GM_DATABASE workers=$GM_WORKERS desktop=$GM_DESKTOP vnc=$GM_VNC"

# -------------------------------------------------------------------
# 1. System packages
# -------------------------------------------------------------------
info "Updating package index..."
apt-get update -qq
# Note: apt-get upgrade is intentionally skipped here. On a full desktop
# image it can take 15+ minutes and timeout SSH connections. Run it
# manually before deploying if desired: sudo apt-get upgrade -y

info "Installing dependencies..."
PACKAGES=(python3 python3-venv python3-dev nginx chromium curl)
if [[ "$GM_DATABASE" == "postgres" ]]; then
    PACKAGES+=(postgresql postgresql-client libpq-dev gcc)
fi
apt-get install -y -qq "${PACKAGES[@]}"

ok "System packages installed."

# -------------------------------------------------------------------
# 2. Application user
# -------------------------------------------------------------------
if ! id "$APP_USER" &>/dev/null; then
    info "Creating application user: $APP_USER"
    useradd --system --create-home --shell /bin/bash "$APP_USER"
fi

# -------------------------------------------------------------------
# 3. Database
# -------------------------------------------------------------------
if [[ "$GM_DATABASE" == "postgres" ]]; then
    info "Configuring PostgreSQL..."
    systemctl enable postgresql
    systemctl start postgresql

    sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='$APP_USER'" | \
        grep -q 1 || sudo -u postgres psql -c "CREATE ROLE $APP_USER WITH LOGIN PASSWORD '$APP_USER';"

    sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='$APP_USER'" | \
        grep -q 1 || sudo -u postgres psql -c "CREATE DATABASE $APP_USER OWNER $APP_USER;"

    if [[ -f "$APP_DIR/pi/postgresql.conf.d/tuning.conf" ]]; then
        PG_CONF_DIR=$(find /etc/postgresql -maxdepth 2 -name main -type d 2>/dev/null | head -1)
        if [[ -n "$PG_CONF_DIR" ]]; then
            mkdir -p "$PG_CONF_DIR/conf.d"
            cp "$APP_DIR/pi/postgresql.conf.d/tuning.conf" "$PG_CONF_DIR/conf.d/"
        fi
        systemctl restart postgresql
    fi
    ok "PostgreSQL configured."
else
    info "Using SQLite — skipping PostgreSQL setup."
    # Stop and disable PostgreSQL if it was previously installed
    if systemctl is-active postgresql &>/dev/null; then
        info "Stopping PostgreSQL (no longer needed)..."
        systemctl stop postgresql
        systemctl disable postgresql
    fi
    ok "SQLite configured (zero-overhead, WAL mode)."
fi

# -------------------------------------------------------------------
# 4. Application directory
# -------------------------------------------------------------------
info "Setting up application directory..."
mkdir -p "$APP_DIR"
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

mkdir -p "$APP_DIR/backend/logs"
chown -R "$APP_USER:$APP_USER" "$APP_DIR/backend/logs"

# SQLite data directory (owned by app user)
if [[ "$GM_DATABASE" == "sqlite" ]]; then
    SQLITE_DATA_DIR="/home/$APP_USER/goodmorning-data"
    sudo -u "$APP_USER" mkdir -p "$SQLITE_DATA_DIR"
fi

# -------------------------------------------------------------------
# 5. Production environment file
# -------------------------------------------------------------------
ENV_FILE="$APP_DIR/backend/.env"
if [[ ! -f "$ENV_FILE" ]]; then
    info "Creating production .env..."
    if [[ -f "$APP_DIR/pi/.env.production" ]]; then
        cp "$APP_DIR/pi/.env.production" "$ENV_FILE"
        # If switching to SQLite, remove DATABASE_URL so Django uses its default
        if [[ "$GM_DATABASE" == "sqlite" ]]; then
            sed -i '/^DATABASE_URL=/d' "$ENV_FILE"
        fi
    else
        {
            echo "DEBUG=False"
            echo "SECRET_KEY=CHANGEME-generate-a-real-secret-key"
            if [[ "$GM_DATABASE" == "postgres" ]]; then
                echo "DATABASE_URL=postgres://goodmorning:goodmorning@localhost:5432/goodmorning"
            fi
            echo "ALLOWED_HOSTS=goodmorning.local,localhost,127.0.0.1"
            echo "FINNHUB_API_KEY="
            echo "USER_CALENDAR="
        } > "$ENV_FILE"
    fi
    chown "$APP_USER:$APP_USER" "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    echo ""
    echo -e "${RED}  *** IMPORTANT: Edit $ENV_FILE with a real SECRET_KEY and your API keys ***${NC}"
    echo ""
else
    # Existing .env — ensure DATABASE_URL matches config
    if [[ "$GM_DATABASE" == "sqlite" ]] && grep -q '^DATABASE_URL=' "$ENV_FILE"; then
        warn "Removing DATABASE_URL from .env (switching to SQLite)..."
        sed -i '/^DATABASE_URL=/d' "$ENV_FILE"
    elif [[ "$GM_DATABASE" == "postgres" ]] && ! grep -q '^DATABASE_URL=' "$ENV_FILE"; then
        warn "Adding DATABASE_URL to .env (switching to PostgreSQL)..."
        echo "DATABASE_URL=postgres://goodmorning:goodmorning@localhost:5432/goodmorning" >> "$ENV_FILE"
    fi
fi

# -------------------------------------------------------------------
# 6. Python venv + dependencies + migrate + seed
# -------------------------------------------------------------------
info "Setting up Python environment..."
sudo -u "$APP_USER" bash -c "
    cd $APP_DIR/backend
    python3 -m venv .venv
    .venv/bin/pip install -q --upgrade pip
    .venv/bin/pip install -q -r requirements.txt
    .venv/bin/python manage.py migrate --no-input
    .venv/bin/python manage.py seed_data
    .venv/bin/python manage.py collectstatic --no-input --clear -v0
"
ok "Application installed."

# -------------------------------------------------------------------
# 7. nginx
# -------------------------------------------------------------------
info "Configuring nginx..."
cp "$APP_DIR/pi/nginx.conf" /etc/nginx/sites-available/goodmorning
ln -sf /etc/nginx/sites-available/goodmorning /etc/nginx/sites-enabled/goodmorning
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl enable nginx
systemctl restart nginx
ok "nginx configured."

# -------------------------------------------------------------------
# 8. systemd services (generated from config)
# -------------------------------------------------------------------
info "Installing systemd services..."

# Generate web service
if [[ "$GM_DATABASE" == "postgres" ]]; then
    WEB_AFTER="After=network.target postgresql.service"
    WEB_REQUIRES="Requires=postgresql.service"
else
    WEB_AFTER="After=network.target"
    WEB_REQUIRES=""
fi

cat > /etc/systemd/system/goodmorning-web.service <<WEBEOF
[Unit]
Description=Good Morning Dashboard — gunicorn
${WEB_AFTER}
${WEB_REQUIRES}

[Service]
Type=notify
User=goodmorning
Group=goodmorning
WorkingDirectory=/opt/goodmorning/backend
Environment=DJANGO_SETTINGS_MODULE=config.settings
ExecStart=/opt/goodmorning/backend/.venv/bin/gunicorn \\
    config.wsgi:application \\
    --bind 127.0.0.1:8000 \\
    --workers ${GM_WORKERS} \\
    --timeout 30 \\
    --access-logfile - \\
    --error-logfile -
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=5
KillMode=mixed

[Install]
WantedBy=multi-user.target
WEBEOF

# Generate scheduler service
if [[ "$GM_DATABASE" == "postgres" ]]; then
    SCHED_AFTER="After=network.target postgresql.service goodmorning-web.service"
    SCHED_REQUIRES="Requires=postgresql.service"
else
    SCHED_AFTER="After=network.target goodmorning-web.service"
    SCHED_REQUIRES=""
fi

cat > /etc/systemd/system/goodmorning-scheduler.service <<SCHEDEOF
[Unit]
Description=Good Morning Dashboard — APScheduler
${SCHED_AFTER}
${SCHED_REQUIRES}

[Service]
Type=simple
User=goodmorning
Group=goodmorning
WorkingDirectory=/opt/goodmorning/backend
Environment=DJANGO_SETTINGS_MODULE=config.settings
ExecStart=/opt/goodmorning/backend/.venv/bin/python \\
    manage.py run_scheduler
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SCHEDEOF

# Remove old kiosk service if present (replaced by XDG autostart)
rm -f /etc/systemd/system/goodmorning-kiosk.service

systemctl daemon-reload
systemctl enable goodmorning-web goodmorning-scheduler
systemctl start goodmorning-web goodmorning-scheduler
ok "Application services started (workers=$GM_WORKERS, database=$GM_DATABASE)."

# -------------------------------------------------------------------
# 9. Kiosk mode (XDG autostart in pi user's desktop session)
# -------------------------------------------------------------------
info "Configuring kiosk mode..."

# Remove old cage/getty kiosk approach if present
rm -f /etc/systemd/system/getty@tty1.service.d/autologin.conf
rmdir /etc/systemd/system/getty@tty1.service.d 2>/dev/null || true
rm -f "/home/$APP_USER/.bash_profile"

# Create XDG autostart entry for the pi user's desktop session.
# This launches Chromium with --start-fullscreen (not --kiosk) so that
# F11 toggles fullscreen and the desktop session remains accessible.
AUTOSTART_DIR="$PI_HOME/.config/autostart"
sudo -u pi mkdir -p "$AUTOSTART_DIR"
sudo -u pi tee "$AUTOSTART_DIR/goodmorning-kiosk.desktop" > /dev/null <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=Good Morning Dashboard
Exec=chromium --ozone-platform=wayland --start-fullscreen --noerrdialogs --disable-translate --no-first-run --disable-infobars --disable-session-crashed-bubble --disable-features=TranslateUI --check-for-update-interval=31536000 --autoplay-policy=no-user-gesture-required --password-store=basic http://localhost
Hidden=false
X-GNOME-Autostart-enabled=true
DESKTOP

# Disable screen blanking
if command -v raspi-config &>/dev/null; then
    raspi-config nonint do_blanking 1 2>/dev/null || true
fi

# Disable DPMS via config.txt
if ! grep -q "hdmi_blanking=2" /boot/firmware/config.txt 2>/dev/null; then
    echo "hdmi_blanking=2" >> /boot/firmware/config.txt
fi

ok "Kiosk mode configured (XDG autostart for pi user)."

# -------------------------------------------------------------------
# 9b. DSI touchscreen rotation (landscape mode)
# -------------------------------------------------------------------
info "Configuring DSI display rotation..."

KANSHI_DIR="$PI_HOME/.config/kanshi"
sudo -u pi mkdir -p "$KANSHI_DIR"
sudo -u pi tee "$KANSHI_DIR/config" > /dev/null <<'KANSHI'
profile dsi-landscape {
    output DSI-2 mode 720x1280 position 0,0 transform 270
}
KANSHI

LABWC_DIR="$PI_HOME/.config/labwc"
sudo -u pi mkdir -p "$LABWC_DIR"
sudo -u pi tee "$LABWC_DIR/rc.xml" > /dev/null <<'LABWC'
<?xml version="1.0"?>
<openbox_config xmlns="http://openbox.org/3.4/rc">
	<touch deviceName="Goodix Capacitive TouchScreen" mapToOutput="DSI-2" mouseEmulation="yes"/>
</openbox_config>
LABWC

ok "DSI display rotation configured (270° landscape via kanshi)."

# -------------------------------------------------------------------
# 9c. Desktop lean mode (disable unused desktop services)
# -------------------------------------------------------------------
if [[ "$GM_DESKTOP" == "lean" ]]; then
    info "Configuring lean desktop mode..."

    # Override the system labwc autostart (/etc/xdg/labwc/autostart) with
    # one that only starts essential services. The system autostart uses
    # lwrespawn which auto-restarts killed processes, so killall won't work.
    # labwc uses ~/.config/labwc/autostart INSTEAD of the system one when present.
    LABWC_AUTOSTART="$LABWC_DIR/autostart"
    sudo -u pi tee "$LABWC_AUTOSTART" > /dev/null <<'AUTOSTART'
# Lean mode: essential services only.
# Omits wf-panel-pi (taskbar), pcmanfm (desktop/file manager), squeekboard (keyboard).
# To revert, delete this file and reboot (or set GM_DESKTOP=full in pi.conf).

/usr/bin/kanshi &
/usr/bin/lxsession-xdg-autostart
AUTOSTART

    ok "Lean desktop: panel, file manager, and on-screen keyboard disabled (~130 MB saved)."
else
    # Full mode: remove lean autostart if present
    rm -f "$PI_HOME/.config/labwc/autostart"
    ok "Full desktop mode: all desktop services enabled."
fi

# -------------------------------------------------------------------
# 9d. VNC remote access
# -------------------------------------------------------------------
if [[ "$GM_VNC" == "off" ]]; then
    info "Disabling VNC (SSH-only remote access)..."
    # rpi-connect runs wayvnc as a user service under the pi user
    sudo -u pi XDG_RUNTIME_DIR="/run/user/$(id -u pi)" \
        systemctl --user disable rpi-connect-wayvnc.service 2>/dev/null || true
    sudo -u pi XDG_RUNTIME_DIR="/run/user/$(id -u pi)" \
        systemctl --user stop rpi-connect-wayvnc.service 2>/dev/null || true
    sudo -u pi XDG_RUNTIME_DIR="/run/user/$(id -u pi)" \
        systemctl --user disable rpi-connect.service 2>/dev/null || true
    sudo -u pi XDG_RUNTIME_DIR="/run/user/$(id -u pi)" \
        systemctl --user stop rpi-connect.service 2>/dev/null || true
    # Also try system-level in case of non-standard install
    systemctl disable wayvnc 2>/dev/null || true
    systemctl stop wayvnc 2>/dev/null || true
    ok "VNC disabled (~43 MB saved)."
else
    ok "VNC enabled (wayvnc for remote desktop access)."
fi

# -------------------------------------------------------------------
# 10. Firewall (optional, if ufw is installed)
# -------------------------------------------------------------------
if command -v ufw &>/dev/null; then
    info "Configuring firewall..."
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw --force enable
    ok "Firewall configured (SSH + HTTP only)."
fi

# -------------------------------------------------------------------
# 11. SSH hardening
# -------------------------------------------------------------------
info "Hardening SSH..."

rm -f /etc/ssh/sshd_config.d/rename_user.conf

sed -i 's/^#\?PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config
for f in /etc/ssh/sshd_config.d/*.conf; do
    [ -f "$f" ] && sed -i 's/^PubkeyAuthentication no/PubkeyAuthentication yes/' "$f"
done

sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config

systemctl reload sshd 2>/dev/null || systemctl reload ssh 2>/dev/null || true
ok "SSH hardened (key auth only, rename_user.conf removed)."

# -------------------------------------------------------------------
# Done
# -------------------------------------------------------------------
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN} Setup complete! Reboot to start the kiosk.${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""
echo "  Configuration:"
echo "    Database:   $GM_DATABASE"
echo "    Workers:    $GM_WORKERS"
echo "    Desktop:    $GM_DESKTOP"
echo "    VNC:        $GM_VNC"
echo ""
echo "  Dashboard:  http://goodmorning.local"
echo "  Admin:      http://goodmorning.local/admin/ (admin/admin)"
echo "  SSH:        ssh goodmorning.local"
echo "  Health:     ssh goodmorning.local /opt/goodmorning/pi/pi-health.sh"
echo ""
echo -e "  ${RED}Remember to edit $APP_DIR/backend/.env with real secrets!${NC}"
echo ""
echo "  Run: sudo reboot"
echo ""
