#!/bin/bash
set -euo pipefail
mkdir -p /var/log/nginx/healthd
chmod 755 /var/log/nginx
# Nginx writes hourly log filenames as its unprivileged worker user.
chown -R 101:101 /var/log/nginx/healthd
