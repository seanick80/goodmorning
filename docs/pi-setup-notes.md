# Raspberry Pi Setup — Lessons Learned

Notes from the first real deployment (2026-03-29). Fixes have been incorporated into the deployment guide and scripts.

---

## Issue 1: `custom.toml` password hash not applied

**Symptom:** Pi booted to desktop logged in as `pi`, but no password was set. `passwd` returned "Authentication token manipulation error" — required `sudo passwd pi`.

**Cause:** The full desktop image (stage5) runs a first-boot wizard that may override or skip `custom.toml` user setup. The `custom.toml` does successfully configure hostname, Wi-Fi, and locale.

**Fix:** Set password manually via `sudo passwd pi` on the Pi terminal. HDMI + USB keyboard required for first boot.

---

## Issue 2: SSH completely blocked on fresh Pi OS (Bookworm+)

**Symptom:** SSH rejected all authentication — both password and public key — despite correct `authorized_keys` permissions, `sshd_config` showing `PubkeyAuthentication yes`, and password being set.

**Root cause:** Raspberry Pi OS Bookworm+ includes `/etc/ssh/sshd_config.d/rename_user.conf` which blocks ALL SSH authentication until the OS detects the default password has been changed through its expected flow. This affects pubkey auth too, not just password auth.

**Fix (two steps required):**
1. `sudo passwd pi` — change from default password
2. `sudo rm -f /etc/ssh/sshd_config.d/rename_user.conf` — remove the SSH block

Both steps are necessary. Changing the password alone is not sufficient because the drop-in config file independently blocks SSH.

**Updated in:** `pi-setup.sh` (section 11), `goodmorning-setup.sh`, deployment guide (Phase 2).

---

## Issue 3: Corrupted `.ssh` directory from failed key install attempts

**Symptom:** `authorized_keys` file ended up in a path with a special character (`/home/pi/<weird char>/.ssh/authorized_keys`) instead of `/home/pi/.ssh/authorized_keys`.

**Cause:** When copying the SSH public key to the Pi via `curl` on the Pi's terminal, shell encoding or locale issues created a directory with a non-ASCII character.

**Fix:** `sudo rm -rf /home/pi/.ssh` followed by running `goodmorning-setup.sh` which recreates the directory cleanly.

**Updated in:** `goodmorning-setup.sh` now does `rm -rf` + fresh `mkdir` instead of appending to avoid this class of issues.

---

## Issue 4: Full desktop image vs Lite

**Impact:** ~200-400 MB additional RAM usage from the desktop environment. Still works on 4 GB Pi (3.5 GB available after boot vs ~3.6 GB on Lite).

**Note:** The desktop environment is useful during initial setup (terminal app, Chromium for testing). Once kiosk mode is configured, the desktop session is replaced by cage+Chromium anyway.

---

## Issue 5: Django 6.0 requires Python 3.12+

**Symptom:** `pip install -r requirements.txt` fails with "No matching distribution found for Django==6.0.3" on Pi.

**Cause:** Raspberry Pi OS Bookworm ships Python 3.11.2. Django 6.0 requires Python 3.12+.

**Fix:** Downgraded to Django 5.2 LTS (supports Python 3.10+) and DRF 3.15.2. No code changes needed — no Django 6.0-specific features were in use.

---

## Issue 6: psycopg-binary has no ARM wheel

**Symptom:** `pip install psycopg-binary==3.3.3` fails on ARM — no prebuilt wheel available.

**Cause:** The `psycopg-binary` package only provides wheels for x86_64. ARM platforms must compile from source or use the pure-Python fallback.

**Fix:** Made `psycopg-binary` conditional in requirements.txt with a platform marker:
```
psycopg==3.3.3
psycopg-binary==3.3.3; platform_machine != "armv7l" and platform_machine != "aarch64"
```
On ARM, `psycopg` runs in pure-Python mode (slightly slower, negligible for this workload). On x86_64 dev machines, `psycopg-binary` provides the fast C extension.

---

## Issue 7: apt-get upgrade times out over SSH

**Symptom:** `pi-setup.sh` starts a full `apt-get upgrade` on the desktop image which takes 15+ minutes. The SSH connection drops and `set -e` kills the script.

**Cause:** Full desktop Pi OS image has hundreds of packages to upgrade (LibreOffice, etc.). Non-interactive SSH with no keepalive drops the connection.

**Fix:** Removed `apt-get upgrade` from the automated setup — run it manually before deploying, or skip it. The `pi-setup.sh` script should only `apt-get install` the specific packages it needs.

---

## Issue 8: Windows line endings break bash scripts on Pi

**Symptom:** `pi-setup.sh` fails with `$'\r': command not found`.

**Cause:** Files created/edited on Windows have CRLF line endings. Bash on Linux requires LF only.

**Fix:** Added `sed -i 's/\r$//' /opt/goodmorning/pi/*.sh` before running scripts. Should also configure git to handle this: `git config core.autocrlf input` or add `.gitattributes`.

---

## Issue 9: No rsync in Git Bash on Windows

**Symptom:** `deploy-pi.sh` fails with `rsync: command not found` when run from Git Bash on Windows.

**Cause:** Git Bash on Windows does not include rsync.

**Fix:** Options:
1. Install rsync via MSYS2: `pacman -S rsync`
2. Run the deploy script from WSL instead of Git Bash
3. For initial deploy, use `scp` + `tar`:
   ```
   tar czf - backend/ frontend/dist/ pi/ | ssh goodmorning@goodmorning.local 'tar xzf - -C /opt/goodmorning/'
   ```

**Updated in:** `deploy-pi.sh` (prerequisite check and documentation).

---

## Issue 10: File ownership issues after deploy

**Symptom:** Application fails to start because files in `/opt/goodmorning/` are owned by `pi` instead of `goodmorning`.

**Cause:** `pi-setup.sh` creates `/opt/goodmorning/` owned by the `goodmorning` system user, but `deploy-pi.sh` copies files over SSH as the `pi` user. The `rsync`/`scp` creates files owned by `pi`.

**Fix:** After initial deploy or any ownership issues:
```
sudo chown -R goodmorning:goodmorning /opt/goodmorning/
```

**Note:** Subsequent deploys via `deploy-pi.sh` should use the `goodmorning` user for SSH (`PI_USER="goodmorning"` in the script), which avoids this issue for ongoing updates. The ownership problem mainly affects initial setup when SSH key is only on the `pi` user.

---

## Issue 11: Kiosk service crash loop on full desktop image

**Symptom:** Screen flashes every ~5 seconds. `journalctl -u goodmorning-kiosk` shows `Missing X server or $DISPLAY` and `Opening in existing browser session` in a restart loop.

**Cause:** The `goodmorning-kiosk.service` launches Chromium as the `goodmorning` system user via cage (Wayland compositor). On a full desktop image, the `pi` user is already logged into the desktop with its own display session. The `goodmorning` user has no display access, so Chromium either fails (`Missing X server`) or opens a tab in the `pi` user's existing Chromium session (which immediately exits, triggering systemd restart).

**Fix:** The cage + systemd kiosk service has been removed entirely. The correct approach is XDG autostart in the `pi` user's desktop session — see Issue 13 for the full story.

**Updated in:** `pi-setup.sh` (kiosk section rewritten), `goodmorning-kiosk.service` deleted from repo, `raspberry-pi-deployment.md` updated.

---

## Issue 12: Deploy procedure wiped the Python venv

**Symptom:** After deploying a backend update via `scp`+`tar`, the application failed to start because the venv was gone. Recreating it on the Pi took several minutes and required PyPI access.

**Root cause:** The manual deploy procedure ran `sudo rm -rf /opt/goodmorning/backend` before extracting the new tarball. This deleted the entire backend directory including `.venv/`, even though the tarball intentionally excluded it.

**Fix:** Extract new code to a temporary directory, copy the existing venv into it, then swap:
1. `tar xzf` into `/opt/goodmorning/backend_new`
2. `cp -a /opt/goodmorning/backend/.venv /opt/goodmorning/backend_new/.venv`
3. `rm -rf /opt/goodmorning/backend && mv backend_new backend`

**Why this matters:** The venv contains platform-specific compiled packages (aarch64). `psycopg` uses the system `libpq`, and `PyJWT[crypto]` needs `cryptography` — both compile native extensions. Recreating the venv on every deploy is slow and may fail if PyPI is flaky or the Pi is offline.

**Also discovered:** `PyJWT[crypto]` was a missing dependency needed for the Google OAuth calendar integration. It was added to `requirements.txt` during the OAuth deploy and compiled successfully on the Pi, but would need to be recompiled if the venv were wiped.

**Updated in:** `reference_pi_access.md` (deploying updates section), `raspberry-pi-deployment.md` (troubleshooting section).

---

## Issue 13: Two Chromium instances — cage kiosk overlaying the desktop

**Symptom:** Chromium appeared fullscreen but F11 did not toggle fullscreen, right-click did not work, and the desktop session was inaccessible. Pressing Ctrl+Alt+F7 revealed the real desktop session running underneath.

**Root cause:** Two separate Chromium instances were running simultaneously:

1. **`goodmorning` system user on tty1:** Getty autologin (`/etc/systemd/system/getty@tty1.service.d/autologin.conf`) logged in the `goodmorning` user, whose `/home/goodmorning/.bash_profile` ran `exec cage -- chromium-browser --kiosk ...`. Cage is a Wayland compositor that runs on tty1 and traps all input. `Restart=always` on systemd AND getty respawning meant it could never be killed.

2. **`pi` user's desktop session:** XDG autostart file at `/home/pi/.config/autostart/goodmorning-kiosk.desktop` launched `chromium-browser --start-fullscreen ...` in the pi user's desktop session (lightdm + labwc/wayfire). This was the correct, intended approach.

The cage instance on tty1 was overlaying the desktop, intercepting all input. It appeared to be the dashboard but was actually a separate, trapped session.

**Fix (already applied to the Pi):**
```bash
# Remove the old kiosk approach
sudo rm -f /home/goodmorning/.bash_profile
sudo rm -f /etc/systemd/system/getty@tty1.service.d/autologin.conf
sudo rm -f /etc/systemd/system/goodmorning-kiosk.service
sudo systemctl daemon-reload
```

**What remains correct on the Pi:**
- `/home/pi/.config/autostart/goodmorning-kiosk.desktop` with `--start-fullscreen`
- `lightdm` display manager running the `pi` user's desktop session
- F11 toggles fullscreen, Ctrl+Alt+F7 returns to graphical desktop from console

**Tip:** If the screen shows a console/command prompt instead of the dashboard, press **Ctrl+Alt+F7** to switch to the graphical desktop.

**Updated in:** `pi-setup.sh` (kiosk section rewritten), `goodmorning-kiosk.service` deleted from repo, `raspberry-pi-deployment.md` (kiosk sections updated).

---

## Updated first-boot sequence

1. Flash Raspberry Pi OS (64-bit) — Lite or Desktop
2. Mount boot partition on dev machine, add: `ssh`, `custom.toml`, `goodmorning-setup.sh`
3. Boot the Pi with HDMI + USB keyboard
4. On the Pi terminal:
   ```
   sudo passwd pi
   sudo rm -f /etc/ssh/sshd_config.d/rename_user.conf
   sudo bash /boot/firmware/goodmorning-setup.sh
   ```
5. From dev machine: `ssh pi@goodmorning.local`
6. Proceed with `pi-setup.sh` and `deploy-pi.sh --setup`
