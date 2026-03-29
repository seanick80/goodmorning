#!/usr/bin/env bash
# goodmorning-setup.sh — Pre-deployment SSH fix for the boot partition.
#
# Copy this file to the SD card's boot partition before first boot.
# After the Pi boots, run on the Pi terminal (HDMI + USB keyboard):
#
#   sudo passwd pi                                # set a non-default password
#   sudo rm -f /etc/ssh/sshd_config.d/rename_user.conf  # remove SSH block
#   sudo bash /boot/firmware/goodmorning-setup.sh        # fix SSH + install key
#
# Then from the dev machine: ssh pi@goodmorning.local
#
# WHY THIS IS NEEDED:
# Raspberry Pi OS (Bookworm+) blocks ALL SSH auth — including public key —
# until the default password is changed. The rename_user.conf drop-in in
# /etc/ssh/sshd_config.d/ enforces this. Simply adding an SSH key is not
# enough. The password must be changed and rename_user.conf must be removed
# before this script will have any effect.
#
# BEFORE USING: Edit the PUBKEY variable below with your dev machine's
# public key (from ~/.ssh/id_ed25519.pub or similar).

set -euo pipefail

# ---- EDIT THIS with your dev machine's public key ----
PUBKEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIP5RKThLX5zLg50KxYEVCmtKnb4gzRKRe3V/WK/h0eVw edgar@goodmorning"

PI_HOME="/home/pi"

echo "=== Fixing SSH ==="

# Remove the Pi OS SSH block (in case it wasn't done manually)
rm -f /etc/ssh/sshd_config.d/rename_user.conf

# Ensure PubkeyAuthentication is enabled
sed -i 's/^#\?PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# Fix any sshd_config.d overrides
for f in /etc/ssh/sshd_config.d/*.conf; do
    [ -f "$f" ] && sed -i 's/^PubkeyAuthentication no/PubkeyAuthentication yes/' "$f"
done

# Ensure authorized_keys path is default
sed -i 's/^#\?AuthorizedKeysFile.*/AuthorizedKeysFile .ssh\/authorized_keys/' /etc/ssh/sshd_config

# Clean and recreate SSH dir (avoids issues with corrupted dirs from failed attempts)
rm -rf "$PI_HOME/.ssh"
mkdir -p "$PI_HOME/.ssh"
chmod 700 "$PI_HOME/.ssh"

# Install the public key
echo "$PUBKEY" > "$PI_HOME/.ssh/authorized_keys"
chmod 600 "$PI_HOME/.ssh/authorized_keys"
chown -R pi:pi "$PI_HOME/.ssh"

# Restart SSH
systemctl restart ssh

echo "=== SSH fixed. Test from dev machine: ssh pi@goodmorning.local ==="
