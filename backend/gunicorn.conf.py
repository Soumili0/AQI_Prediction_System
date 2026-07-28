"""
Gunicorn configuration for production deployment.
Used by Render, Docker, and any WSGI host.
"""

import multiprocessing
import os

# Server socket
bind    = f"0.0.0.0:{os.getenv('PORT', '5000')}"
backlog = 2048

# Workers
workers          = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class     = "sync"
worker_connections = 1000
threads          = 2
timeout          = 120
keepalive        = 5

# Restart workers after this many requests (prevents memory leaks)
max_requests      = 1000
max_requests_jitter = 100

# Logging
accesslog = "-"       # stdout
errorlog  = "-"       # stderr
loglevel  = os.getenv("LOG_LEVEL", "info").lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sµs'

# Process naming
proc_name = "aqi_prediction_api"

# Security
limit_request_line   = 4096
limit_request_fields = 100

# Hooks
def on_starting(server):
    server.log.info("AQI Prediction API starting…")

def post_fork(server, worker):
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def worker_exit(server, worker):
    server.log.info(f"Worker exited (pid: {worker.pid})")
