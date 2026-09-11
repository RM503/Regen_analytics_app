# Gunicorn configuration file

import multiprocessing
import os

port = os.environ.get("PORT", 8080)

bind = f"0.0.0.0:{port}"
timeout = 600
workers = int(os.getenv("WEB_CONCURRENCY", multiprocessing.cpu_count() * 2 + 1))
threads = int(os.getenv("GUNICORN_THREADS", "2"))
worker_class = "gthread"
preload_app = True
