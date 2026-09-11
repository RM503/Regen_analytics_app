#!/bin/bash
set -euo pipefail
cd /var/app/current
docker compose exec -T app python -c '
import urllib.request
for path in ("/", "/initial_market_data/", "/polygon_generator/", "/farmland_characteristics/", "/farmland_statistics/"):
    response = urllib.request.urlopen("http://nginx" + path, timeout=30)
    assert response.status == 200, path
    print(path, response.status)
'
docker compose exec -T celery celery -A regen_queue.celery_app inspect ping --timeout 15
