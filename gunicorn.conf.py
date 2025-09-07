# Gunicorn configuration file

import multiprocessing 

bind = "0.0.0.0:8000"
timeout = 120
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gthread"
preload_app = True