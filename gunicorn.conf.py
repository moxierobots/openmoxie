# Gunicorn configuration file for OpenMoxie
import multiprocessing
import os
from psycogreen.gevent import patch_psycopg     # use this if you use gevent workers

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = 1
worker_class = "gevent"
worker_connections = 10
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "openmoxie"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Performance
preload_app = True

# Graceful shutdown
graceful_timeout = 30

def post_fork(server, worker):
    patch_psycopg()
    worker.log.info("Made Psycopg2 Green")
