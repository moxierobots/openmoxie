# Gunicorn configuration file for OpenMoxie
from gevent import monkey
monkey.patch_all()
# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = 1
worker_class = "gevent"
worker_connections = 50
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

# Worker lifecycle hooks
def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info("Worker received INT or QUIT signal")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    worker.log.info("Worker received SIGABRT signal")

def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Forking new master process")

def pre_request(worker, req):
    """Called just before a worker processes the request."""
    worker.log.debug(f"{req.method} {req.path}")

def post_request(worker, req, environ, resp):
    """Called after a worker processes the request."""
    worker.log.debug(f"Response: {resp.status_code}")

def child_exit(server, worker):
    """Called just after a worker has been exited."""
    server.log.info(f"Worker exited (pid: {worker.pid})")
