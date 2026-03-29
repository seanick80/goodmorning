#!/usr/bin/env bash
# pi-setup.sh — One-time bootstrap for Raspberry Pi 5.
#
# Run this on the Pi after first boot:
#   ssh goodmorning.local 'bash -s' < pi/pi-setup.sh
#
# Or copy it to the Pi and run:
#   sudo bash /opt/goodmorning/pi/pi-setup.sh
#
# Prerequisites: Raspberry Pi OS Lite (64-bit), SSH enabled, Wi-Fi configured.

set -euo pipefail

APP_DIR="/opt/goodmorning"
APP_USER="goodmorning"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

info() { echo -e "${CYAN}[setup]${NC} $*"; }
ok()   { echo -e "${GREEN}[setup]${NC} $*"; }
fail() { echo -e "${RED}[setup]${NC} $*"; exit 1; }

# Must run as root
if [[ $EUID -ne 0 ]]; then
    fail "This script must be run as root (use sudo)."
fi

# -------------------------------------------------------------------
# 1. System packages
# -------------------------------------------------------------------
info "Updating package index..."
apt-get update -qq
# Note: apt-get upgrade is intentionally skipped here. On a full desktop
# image it can take 15+ minutes and timeout SSH connections. Run it
# manually before deploying if desired: sudo apt-get upgrade -y

info "Installing dependencies..."
apt-get install -y -qq \
    python3 python3-venv python3-dev \
    postgresql postgresql-client \
    nginx \
    chromium-browser \
    cage \
    libpq-dev gcc \
    curl

ok "System packages installed."

# -------------------------------------------------------------------
# 2. Application user
# -------------------------------------------------------------------
if ! id "$APP_USER" &>/dev/null; then
    info "Creating application user: $APP_USER"
    useradd --system --create-home --shell /bin/bash "$APP_USER"
fi

# -------------------------------------------------------------------
# 3. PostgreSQL
# -------------------------------------------------------------------
info "Configuring PostgreSQL..."

# Ensure PostgreSQL is running
systemctl enable postgresql
systemctl start postgresql

# Create database user and database (idempotent)
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='$APP_USER'" | \
    grep -q 1 || sudo -u postgres psql -c "CREATE ROLE $APP_USER WITH LOGIN PASSWORD '$APP_USER';"

sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='$APP_USER'" | \
    grep -q 1 || sudo -u postgres psql -c "CREATE DATABASE $APP_USER OWNER $APP_USER;"

# Install tuning config
if [[ -f "$APP_DIR/pi/postgresql.conf.d/tuning.conf" ]]; then
    mkdir -p /etc/postgresql/16/main/conf.d
    cp "$APP_DIR/pi/postgresql.conf.d/tuning.conf" /etc/postgresql/16/main/conf.d/
    systemctl restart postgresql
fi

ok "PostgreSQL configured."

# -------------------------------------------------------------------
# 4. Application directory
# -------------------------------------------------------------------
info "Setting up application directory..."
mkdir -p "$APP_DIR"
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# Create log directory
mkdir -p "$APP_DIR/backend/logs"
chown -R "$APP_USER:$APP_USER" "$APP_DIR/backend/logs"

# -------------------------------------------------------------------
# 5. Production environment file
# -------------------------------------------------------------------
ENV_FILE="$APP_DIR/backend/.env"
if [[ ! -f "$ENV_FILE" ]]; then
    info "Creating production .env (you should edit this)..."
    if [[ -f "$APP_DIR/pi/.env.production" ]]; then
        cp "$APP_DIR/pi/.env.production" "$ENV_FILE"
    else
        cat > "$ENV_FILE" <<'ENVEOF'
DEBUG=False
SECRET_KEY=CHANGEME-generate-a-real-secret-key
DATABASE_URL=postgres://goodmorning:goodmorning@localhost:5432/goodmorning
ALLOWED_HOSTS=goodmorning.local,localhost,127.0.0.1
FINNHUB_API_KEY=
WEATHER_LAT=40.7128
WEATHER_LON=-74.0060
USER_CALENDAR=
ENVEOF
    fi
    chown "$APP_USER:$APP_USER" "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    echo ""
    echo -e "${RED}  *** IMPORTANT: Edit $ENV_FILE with a real SECRET_KEY and your API keys ***${NC}"
    echo ""
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
# 8. systemd services
# -------------------------------------------------------------------
info "Installing systemd services..."
cp "$APP_DIR/pi/goodmorning-web.service" /etc/systemd/system/
cp "$APP_DIR/pi/goodmorning-scheduler.service" /etc/systemd/system/
cp "$APP_DIR/pi/goodmorning-kiosk.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable goodmorning-web goodmorning-scheduler
systemctl start goodmorning-web goodmorning-scheduler
ok "Application services started."

# -------------------------------------------------------------------
# 9. Kiosk mode
# -------------------------------------------------------------------
info "Configuring kiosk mode..."

# Auto-login for kiosk user via cage (Wayland compositor)
mkdir -p /etc/systemd/system/getty@tty1.service.d
cat > /etc/systemd/system/getty@tty1.service.d/autologin.conf <<EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $APP_USER --noclear %I \$TERM
EOF

# Create .bash_profile that starts cage+chromium on login at tty1
sudo -u "$APP_USER" bash -c "
cat > /home/$APP_USER/.bash_profile <<'PROFILE'
# Start kiosk on tty1 only
if [ \"\$(tty)\" = \"/dev/tty1\" ]; then
    exec cage -- chromium-browser \\
        --kiosk \\
        --noerrdialogs \\
        --disable-translate \\
        --no-first-run \\
        --disable-infobars \\
        --disable-session-crashed-bubble \\
        --disable-features=TranslateUI \\
        --check-for-update-interval=31536000 \\
        --autoplay-policy=no-user-gesture-required \\
        --password-store=basic \\
        http://localhost
fi
PROFILE
"

# Disable screen blanking
if command -v raspi-config &>/dev/null; then
    raspi-config nonint do_blanking 1 2>/dev/null || true
fi

# Disable DPMS via config.txt
if ! grep -q "hdmi_blanking=2" /boot/firmware/config.txt 2>/dev/null; then
    echo "hdmi_blanking=2" >> /boot/firmware/config.txt
fi

ok "Kiosk mode configured."

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

# Remove the Raspberry Pi OS SSH block that prevents all auth (including
# pubkey) when the default password is unchanged. This drop-in file is
# present on Bookworm+ images and must be removed for SSH to work.
rm -f /etc/ssh/sshd_config.d/rename_user.conf

# Ensure pubkey auth is enabled (some Pi OS images disable it by default)
sed -i 's/^#\?PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config
for f in /etc/ssh/sshd_config.d/*.conf; do
    [ -f "$f" ] && sed -i 's/^PubkeyAuthentication no/PubkeyAuthentication yes/' "$f"
done

# Disable password auth (key-only from here on)
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
echo "  Dashboard:  http://goodmorning.local"
echo "  Admin:      http://goodmorning.local/admin/ (admin/admin)"
echo "  SSH:        ssh goodmorning.local"
echo "  Health:     ssh goodmorning.local /opt/goodmorning/pi/pi-health.sh"
echo ""
echo -e "  ${RED}Remember to edit $APP_DIR/backend/.env with real secrets!${NC}"
echo ""
echo "  Run: sudo reboot"
echo ""
