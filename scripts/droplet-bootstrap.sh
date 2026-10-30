#!/usr/bin/env bash
# One-time, idempotent setup of a fresh Ubuntu LTS Droplet. Run as root (the Droplet's initial ssh key is already on root):
#   scp scripts/droplet-bootstrap.sh root@<ip>:/root/ && ssh root@<ip> 'bash /root/droplet-bootstrap.sh'
# Safe to run again. It does not touch /srv/labourlens/.env or the data directory contents.
#
# What it does: deploy user (uid 10001, the same uid the app container runs as), /srv/labourlens tree, Docker Engine and the
# compose plugin from Docker's apt repository, unattended security upgrades, ufw (22/80/443 only), fail2ban for sshd,
# key-only ssh, and a 1 GiB swap file.
set -euo pipefail

[ "$(id -u)" -eq 0 ] || { echo "run as root" >&2; exit 1; }
. /etc/os-release
[ "${ID:-}" = ubuntu ] || { echo "this script supports Ubuntu only (found: ${ID:-unknown})" >&2; exit 1; }

DEPLOY_USER=deploy
DEPLOY_UID=10001   # must equal the user the container runs as (Dockerfile USER 10001) so the app can write the bind-mounted data/
APP_ROOT=/srv/labourlens
export DEBIAN_FRONTEND=noninteractive

echo "== packages"
apt-get update -qq
apt-get install -y -qq ca-certificates curl gnupg ufw fail2ban unattended-upgrades rsync

echo "== deploy user"
if ! id "$DEPLOY_USER" >/dev/null 2>&1; then
  groupadd --gid "$DEPLOY_UID" "$DEPLOY_USER"
  useradd --uid "$DEPLOY_UID" --gid "$DEPLOY_UID" --create-home --shell /bin/bash "$DEPLOY_USER"
fi
install -d -m 700 -o "$DEPLOY_USER" -g "$DEPLOY_USER" "/home/$DEPLOY_USER/.ssh"
auth="/home/$DEPLOY_USER/.ssh/authorized_keys"
if [ ! -s "$auth" ]; then
  [ -s /root/.ssh/authorized_keys ] || { echo "no ssh key on root to copy; add one to /root/.ssh/authorized_keys first (refusing to disable passwords)" >&2; exit 1; }
  install -m 600 -o "$DEPLOY_USER" -g "$DEPLOY_USER" /root/.ssh/authorized_keys "$auth"
fi

echo "== application tree"
install -d -m 750 -o "$DEPLOY_USER" -g "$DEPLOY_USER" "$APP_ROOT" "$APP_ROOT/deploy" "$APP_ROOT/state" "$APP_ROOT/data" "$APP_ROOT/backups"

echo "== docker engine and compose plugin (Docker's apt repository)"
if ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${UBUNTU_CODENAME:-$VERSION_CODENAME} stable" > /etc/apt/sources.list.d/docker.list
  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi
systemctl enable --now docker
# Membership in the docker group is root-equivalent on this host. It is needed for the deploy job; keep the deploy key private.
usermod -aG docker "$DEPLOY_USER"

echo "== unattended security upgrades"
cat > /etc/apt/apt.conf.d/20auto-upgrades <<'CONF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
CONF

echo "== ssh: key-only login"
cat > /etc/ssh/sshd_config.d/00-labourlens.conf <<'CONF'
# Named 00- so it is read before cloud-init's 50-cloud-init.conf (first value wins in sshd).
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin prohibit-password
PubkeyAuthentication yes
CONF
sshd -t
systemctl reload ssh 2>/dev/null || systemctl reload sshd

echo "== fail2ban (sshd)"
cat > /etc/fail2ban/jail.d/labourlens-sshd.local <<'CONF'
[sshd]
enabled = true
backend = systemd
maxretry = 5
findtime = 10m
bantime = 1h
CONF
systemctl enable --now fail2ban
systemctl restart fail2ban

echo "== firewall (ufw): 22, 80, 443"
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "== swap (1 GiB)"
if ! swapon --show --noheadings | grep -q .; then
  if [ ! -f /swapfile ]; then
    fallocate -l 1G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile >/dev/null
  fi
  swapon /swapfile
fi
grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
echo 'vm.swappiness=10' > /etc/sysctl.d/99-labourlens.conf
sysctl -q -p /etc/sysctl.d/99-labourlens.conf

echo
echo "bootstrap complete."
echo "Open a SECOND terminal and confirm 'ssh $DEPLOY_USER@<ip>' works before closing this session."
echo "Note: Docker publishes container ports by editing iptables itself, so ufw does not filter them. Only Caddy publishes ports (80/443);"
echo "      also set the DigitalOcean cloud firewall as a second layer (docs/deploy.md)."
