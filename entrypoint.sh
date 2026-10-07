#!/bin/bash
set -e

mkdir -p /var/log/app /var/run/fail2ban /etc/fail2ban/filter.d
touch /var/log/app/access.log /var/log/fail2ban.log
rm -f /var/run/fail2ban/fail2ban.sock /var/run/fail2ban/fail2ban.pid

# Start fail2ban server
fail2ban-client -x start || echo "[WARN] Fail2ban could not start with iptables. Ensure NET_ADMIN capability is provided."

echo "[books-dashboard-api] Fail2ban initialized. Starting Uvicorn API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8001
