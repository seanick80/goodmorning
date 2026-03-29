# Raspberry Pi 5 Deployment Plan

## Target Hardware

- Raspberry Pi 5, 4 GB RAM
- Official touchscreen display
- microSD card (32 GB+)
- Connected to local Wi-Fi

### Python Compatibility

Raspberry Pi OS Bookworm ships Python 3.11.2. Django 5.2 LTS is used (not 6.0) for compatibility. The `psycopg-binary` package has no ARM wheel, so `requirements.txt` uses a platform marker to install it only on x86_64; on ARM, the pure-Python `psycopg` driver is used instead.

## Goals

1. **Initial setup** — flash SD card, run one script, dashboard is live
2. **One-touch updates** — from the Windows dev machine, push code + restart over SSH
3. **Kiosk mode** — Pi boots directly into a fullscreen Chromium showing the dashboard
4. **Unattended** — auto-recovers from power loss, network drops, and crashes

---

## Architecture on the Pi

```
┌────────────────────────────────────────────────────┐
│ Raspberry Pi 5                                     │
│                                                    │
│  systemd                                           │
│  ├── goodmorning-web.service   (gunicorn, 2 workers)
│  ├── goodmorning-scheduler.service (APScheduler)   │
│  └── goodmorning-kiosk.service (Chromium fullscreen)│
│                                                    │
│  nginx (port 80)                                   │
│  ├── /           → frontend/dist/ (static files)   │
│  └── /api/, /admin/ → gunicorn (port 8000)         │
│                                                    │
│  PostgreSQL 16 (native, not Docker)                │
│  └── goodmorning database                          │
└────────────────────────────────────────────────────┘
```

### Why this stack (not Docker on the Pi)

| Approach | Pros | Cons |
|----------|------|------|
| **Docker on Pi** | Same as dev | ~500 MB overhead, ARM image quirks, swap pressure on 4 GB, slower startup |
| **Native services (chosen)** | Minimal overhead, fast boot, systemd auto-restart, simple debugging | Different from dev environment |

Docker on a 4 GB Pi adds memory pressure and boot time for little benefit when the stack is just Python + PostgreSQL + nginx. Native systemd services start in seconds and are trivial to monitor.

### Why PostgreSQL (not SQLite)

SQLite could work for reads, but APScheduler + gunicorn workers create concurrent write contention. PostgreSQL handles this cleanly and is already the dev database. On a Pi 5, PostgreSQL uses ~50 MB RAM idle — well within budget.

### Why nginx (not WhiteNoise-only)

WhiteNoise can serve static files from Django, but nginx is better at:
- Serving the SPA `index.html` for all non-API routes (client-side routing)
- Gzip compression with zero Python overhead
- Connection buffering (protects gunicorn from slow clients)
- Serving the ~260 KB frontend bundle with proper cache headers

---

## Memory Budget (4 GB)

| Component | Estimate |
|-----------|----------|
| Raspberry Pi OS | ~400 MB |
| PostgreSQL 16 | ~50 MB |
| gunicorn (2 workers) | ~120 MB |
| APScheduler process | ~60 MB |
| nginx | ~10 MB |
| Chromium (kiosk) | ~300 MB |
| **Total** | **~940 MB** |
| **Headroom** | **~3 GB** |

Comfortable margin. No swap needed under normal operation.

---

## File Layout on the Pi

```
/opt/goodmorning/
├── backend/              # Django app (copied from repo)
│   ├── .venv/            # Python venv (built on Pi)
│   ├── config/
│   ├── dashboard/
│   ├── manage.py
│   └── .env              # Production environment
├── frontend/
│   └── dist/             # Pre-built static files (built on dev machine)
├── pi/                   # Pi-specific config files
│   ├── nginx.conf
│   ├── goodmorning-web.service
│   ├── goodmorning-scheduler.service
│   └── goodmorning-kiosk.service
└── pi-update.sh          # On-Pi update script
```

---

## Initial Setup Process

### Phase 1: Prepare the SD card (on dev machine)

1. Flash Raspberry Pi OS (64-bit) using Raspberry Pi Imager (Lite recommended, full desktop also works — desktop uses ~200-400 MB more RAM but is fine on 4 GB)
2. Mount the boot partition (FAT32, visible as a drive letter on Windows)
3. Create a `custom.toml` on the boot partition for first-boot configuration:
   ```toml
   [system]
   hostname = "goodmorning"

   [user]
   name = "pi"
   password = "<encrypted password hash>"
   password_encrypted = true

   [ssh]
   enabled = true
   password_authentication = true

   [wlan]
   ssid = "<your Wi-Fi SSID>"
   password = "<your Wi-Fi password>"
   password_encrypted = false
   country = "<2-letter country code>"

   [locale]
   timezone = "<timezone e.g. Australia/Hobart>"
   keymap = "us"
   ```
4. Create an empty `ssh` file on the boot partition (enables SSH on first boot)
5. Copy `pi/goodmorning-setup.sh` to the boot partition (SSH fix + key install)
6. Generate an SSH key on the dev machine if you don't have one: `ssh-keygen -t ed25519`
7. Edit `goodmorning-setup.sh` to include your public key from `~/.ssh/id_ed25519.pub`
8. Back up original `config.txt` and `cmdline.txt` (optional, nothing is modified)
9. Populate `pi/.env.production` with real secrets (SECRET_KEY, API keys, calendar URL, coordinates) — this file is gitignored and must be configured manually

### Phase 2: First boot (HDMI + USB keyboard required)

The `custom.toml` password hash may not be applied on all Pi OS images (especially full desktop). An HDMI display and USB keyboard are needed for the first boot to fix SSH access.

1. Insert the SD card and power on the Pi
2. Wait for it to boot and connect to Wi-Fi (hostname and Wi-Fi from `custom.toml` do work)
3. On the Pi terminal, set the `pi` user password (required — SSH is blocked until this is done):
   ```
   sudo passwd pi
   ```
4. Remove the SSH security block that prevents login when the default password is unchanged:
   ```
   sudo rm -f /etc/ssh/sshd_config.d/rename_user.conf
   ```
5. Run the setup script to configure SSH key auth:
   ```
   sudo bash /boot/firmware/goodmorning-setup.sh
   ```
6. From the dev machine, verify SSH works:
   ```
   ssh pi@goodmorning.local
   ```

**Why this is needed:** Raspberry Pi OS (Bookworm+) blocks all SSH authentication — including public key — until the default password is changed. The `rename_user.conf` drop-in in `/etc/ssh/sshd_config.d/` enforces this. Simply adding an SSH key is not enough.

### Phase 3: Application setup (via SSH from dev machine)

A single `pi-setup.sh` script runs on the Pi (pushed via SSH or curl) that:

1. **System packages:**
   ```
   apt-get update
   apt-get install python3 python3-venv python3-dev postgresql postgresql-client nginx chromium-browser cage libpq-dev gcc curl
   ```
   **Note:** `apt-get upgrade` is intentionally omitted. On a full desktop image it takes 15+ minutes and can timeout SSH connections. Run it manually before deploying if desired.

2. **PostgreSQL:**
   - Create `goodmorning` database and user
   - Tune for Pi (shared_buffers=128MB, work_mem=4MB)

3. **Application:**
   - Create `/opt/goodmorning/` directory structure
   - Create Python venv, install requirements
   - Copy production `.env`
   - Run migrations + seed data

4. **nginx:**
   - Install config to serve frontend on `/` and proxy `/api/` to gunicorn

5. **systemd services:**
   - Install and enable `goodmorning-web`, `goodmorning-scheduler`, `goodmorning-kiosk`

6. **Kiosk mode:**
   - Install minimal X11/Wayland session
   - Auto-login to kiosk user
   - Chromium launches fullscreen pointing at `http://localhost`
   - Disable screen blanking / power management

7. **Reboot** — dashboard should be live

### What the Pi-setup script does NOT do

- Install Docker (not needed)
- Build the frontend (done on dev machine, only `dist/` is deployed)
- Touch the dev machine's `.env` (Pi gets its own production `.env`)

---

## One-Touch Update Process

### From the Windows dev machine

```bash
./deploy-pi.sh                    # Default: update code + restart
./deploy-pi.sh --full             # Full redeploy (deps + migrations + restart)
./deploy-pi.sh --frontend-only    # Just rebuild and push frontend
./deploy-pi.sh --restart          # Just restart services
```

### What `deploy-pi.sh` does

```
Dev machine                              Raspberry Pi
──────────                               ────────────
1. npm run build (frontend/dist/)
2. rsync backend/ → Pi:/opt/goodmorning/backend/
   rsync frontend/dist/ → Pi:/opt/goodmorning/frontend/dist/
   rsync pi/ → Pi:/opt/goodmorning/pi/
3. SSH: pi-update.sh ─────────────────→  4. pip install -r requirements.txt
                                          5. python manage.py migrate
                                          6. python manage.py collectstatic
                                          7. systemctl restart goodmorning-*
                                          8. Health check: curl localhost/api/weather/
```

### Key design decisions

- **rsync over SSH** — fast incremental sync, only changed files transfer. **Note:** rsync is not available in Git Bash on Windows. Install it via MSYS2/pacman (`pacman -S rsync`), use WSL, or use the `scp`+`tar` fallback built into `deploy-pi.sh`
- **Frontend built on dev machine** — Pi doesn't need Node.js installed (saves ~200 MB + build time)
- **No downtime** — gunicorn restarts gracefully (workers finish current requests)
- **Health check** — script waits for the API to respond before reporting success
- **No git on Pi** — the Pi receives built artifacts, not a repo clone. This avoids needing git, avoids `.git` bloat, and prevents accidental edits on the Pi diverging from the repo.

---

## Alternative: Git pull on Pi

| Aspect | rsync artifacts (chosen) | git pull on Pi |
|--------|------------------------|----------------|
| Node.js on Pi | Not needed | Required for frontend build |
| Pi disk usage | ~15 MB (app + dist) | ~250 MB (repo + node_modules + .venv) |
| Deploy speed | ~5 seconds (rsync delta) | ~60 seconds (pull + npm build + pip) |
| Complexity | Simple, predictable | Merge conflicts possible |
| Rollback | Keep previous rsync'd copy | `git revert` |

rsync wins on simplicity and speed. The Pi is a deployment target, not a dev machine.

---

## Alternative: Docker Compose on Pi

Already covered above. Summary: Docker adds ~500 MB memory overhead and slower cold boot for a single-purpose appliance. Native services are the right call for a dedicated kiosk with 4 GB RAM.

---

## Kiosk Mode Details

The Pi runs as a single-purpose dashboard display:

- **Auto-login** to a `kiosk` user (no desktop environment)
- **Cage or labwc** (lightweight Wayland compositor) launches Chromium in fullscreen
- **Chromium flags:** `--kiosk --noerrdialogs --disable-translate --no-first-run`
- **Touchscreen:** No custom touch handling — Chromium handles touch natively on Wayland. Standard browser gestures (scroll, tap) work out of the box. No swipe/gesture features for now; the user may want to swipe to YouTube/Spotify in the future, which would be a separate browser tab or app-switcher feature.
- **Screen always on:** disable DPMS and screen blanking
- **Crash recovery:** systemd `Restart=always` on all services
- **Power loss:** Pi boots → systemd starts services → Chromium opens dashboard

---

## Security Considerations

- SSH key auth only (disable password auth after setup)
- PostgreSQL listens on localhost only
- nginx serves on port 80 (LAN only, no internet exposure)
- Production `.env` has a real `SECRET_KEY` and `DEBUG=False`
- `ALLOWED_HOSTS` set to `goodmorning.local,<Pi-IP>`
- Firewall: only ports 22 (SSH) and 80 (HTTP) open

---

## Stale Data Indicator

When the dashboard's cached data hasn't been refreshed in over 20 minutes (e.g., Wi-Fi drops, API outage), the frontend displays a small red indicator icon. This keeps the dashboard useful with cached data while making staleness visible at a glance.

**Implementation:**
- Each API response already includes a `fetched_at` timestamp
- Frontend compares `fetched_at` to current time
- If any widget's data is >20 minutes old, show a subtle red dot/icon in that widget's header
- No overlay, no blocking — the dashboard remains fully readable

This is a frontend-only change (no backend work needed).

---

## Remote Health Check

Health monitoring via SSH from the dev machine — no API endpoint needed.

**`pi/pi-health.sh`** — a script on the Pi that prints a status summary:

```
$ ssh goodmorning.local /opt/goodmorning/pi/pi-health.sh

Good Morning Dashboard — Health Check
──────────────────────────────────────
Uptime:       12 days, 3:42
Services:
  web          active (running) since Mon 2026-03-13 08:00:01
  scheduler    active (running) since Mon 2026-03-13 08:00:02
  kiosk        active (running) since Mon 2026-03-13 08:00:05
Database:      OK (5 tables, 847 rows)
Last fetch:
  weather      2 min ago
  stocks       4 min ago
  calendar     18 min ago
  news         42 min ago
Disk:          3.2G / 29G (11%)
Memory:        941M / 3.7G (25%)
```

From the dev machine, invoke with: `ssh goodmorning.local /opt/goodmorning/pi/pi-health.sh`

Alternatively, `deploy-pi.sh --status` can wrap this SSH call for convenience.

---

## Log Access

Logs are accessed via SSH + journalctl:

```bash
# All goodmorning services
ssh goodmorning.local journalctl -u 'goodmorning-*' --since '1 hour ago'

# Just the web server
ssh goodmorning.local journalctl -u goodmorning-web -f    # follow live

# Just the scheduler
ssh goodmorning.local journalctl -u goodmorning-scheduler --since today
```

Django file-based logs are also at `/opt/goodmorning/backend/logs/` and can be read with `ssh goodmorning.local cat /opt/goodmorning/backend/logs/errors.log`.

---

## Files to Create

| File | Purpose |
|------|---------|
| `pi/pi-setup.sh` | One-time Pi bootstrap (packages, DB, services, kiosk) |
| `pi/pi-update.sh` | On-Pi script: install deps, migrate, restart |
| `pi/pi-health.sh` | On-Pi script: print system/service/data status summary |
| `pi/nginx.conf` | nginx site config (static + API proxy) |
| `pi/goodmorning-web.service` | systemd unit for gunicorn |
| `pi/goodmorning-scheduler.service` | systemd unit for APScheduler |
| `pi/goodmorning-kiosk.service` | systemd unit for Chromium kiosk |
| `pi/postgresql.conf.d/tuning.conf` | PostgreSQL Pi tuning overrides |
| `pi/.env.production` | Template production environment |
| `deploy-pi.sh` | Dev-machine script: build, rsync, trigger update |

---

## Decisions

| Question | Decision |
|----------|----------|
| Touchscreen | No custom touch features. Chromium handles standard gestures. May add app-switching (YouTube/Spotify) later. |
| Remote monitoring | SSH-based health script (`pi-health.sh`), no API endpoint. `deploy-pi.sh --status` wraps the SSH call. |
| Wi-Fi resilience | Display cached data; show a red stale-data icon per widget when `fetched_at` is >20 minutes old. |
| Multiple Pis | Single Pi — no parameterization needed. Hostname hardcoded to `goodmorning.local`. |
| Log access | SSH + journalctl. Django file logs also available at `/opt/goodmorning/backend/logs/`. |

---

## Troubleshooting

Common issues encountered during the first real deployment. See also `docs/pi-setup-notes.md` for detailed root cause analysis.

### SSH rejected — "Permission denied" for all auth methods

Raspberry Pi OS Bookworm+ includes `/etc/ssh/sshd_config.d/rename_user.conf` which blocks ALL SSH authentication (including pubkey) until the default password is changed. Fix on the Pi terminal (HDMI + keyboard required):

```bash
sudo passwd pi
sudo rm -f /etc/ssh/sshd_config.d/rename_user.conf
sudo systemctl reload ssh
```

### `custom.toml` password not applied

The full desktop Pi OS image may skip the password hash from `custom.toml` (hostname, Wi-Fi, and locale do work). Set password manually on first boot: `sudo passwd pi`.

### `pip install` fails with "No matching distribution for Django==6.0"

Pi OS Bookworm ships Python 3.11.2. Django 6.0 requires Python 3.12+. The project uses Django 5.2 LTS for Pi compatibility.

### `pip install psycopg-binary` fails on ARM

No prebuilt ARM wheel exists. The `requirements.txt` uses a platform marker to skip `psycopg-binary` on ARM. The pure-Python `psycopg` driver works on all platforms.

### Bash scripts fail with `$'\r': command not found`

Windows CRLF line endings. Fix before running on Pi:
```bash
sed -i 's/\r$//' /opt/goodmorning/pi/*.sh
```
The project `.gitattributes` enforces LF endings for `.sh` files, but this only works if the file was checked out after the `.gitattributes` was added.

### `rsync: command not found` in Git Bash on Windows

Git Bash on Windows does not include rsync. Options:
1. Install rsync via MSYS2: `pacman -S rsync`
2. Use WSL for the deploy script
3. Use `scp` + `tar` for initial deploy: `tar czf - backend/ | ssh pi@goodmorning.local 'tar xzf - -C /opt/goodmorning/'`

### `apt-get upgrade` times out over SSH

Full desktop image has hundreds of packages. Run upgrade manually on the Pi terminal instead of over SSH, or use `screen`/`tmux` to survive disconnects.

### File ownership issues after deploy

`pi-setup.sh` creates `/opt/goodmorning/` owned by the `goodmorning` user, but `deploy-pi.sh` copies files as the `pi` user via SSH. After initial deploy, fix ownership:
```bash
sudo chown -R goodmorning:goodmorning /opt/goodmorning/
```

### Corrupted `.ssh` directory

If SSH key installation created directories with special characters (encoding issues from terminal copy-paste), remove and recreate:
```bash
rm -rf ~/.ssh
mkdir -p ~/.ssh && chmod 700 ~/.ssh
```
Then re-run `goodmorning-setup.sh`.