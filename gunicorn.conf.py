# Gunicorn configuration file

import multiprocessing
import os

port = os.environ.get("PORT", 8000)

bind = f"0.0.0.0:{port}"
timeout = 120
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gthread"
preload_app = True