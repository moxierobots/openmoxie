# OpenMoxie Deployment Guide

This document describes how to deploy OpenMoxie using Gunicorn with gevent workers for production environments.

## Overview

OpenMoxie now uses Gunicorn with gevent workers instead of the Django development server for better performance and scalability. The setup includes:

- **Gunicorn** as the WSGI HTTP server
- **Gevent** worker class for async I/O handling
- **10 greenlets** per worker for concurrent request handling
- **Separated migration jobs** for better deployment practices

## Architecture

### Components

1. **MQTT Service**: Handles MQTT message broker functionality
2. **Migration Service**: Runs database migrations and data initialization as a one-time job
3. **Web Server**: Runs the Django application using Gunicorn with gevent workers

### Worker Configuration

- **Worker Class**: `gevent` for asynchronous I/O
- **Worker Connections**: 10 greenlets per worker
- **Workers**: 1 (can be scaled based on CPU cores)
- **Max Requests**: 1000 requests per worker before restart
- **Timeout**: 30 seconds for request handling

## Deployment Options

### Docker Compose (Recommended)

#### Quick Start
```bash
# Run the full stack
docker-compose up

# Run migrations only
docker-compose --profile migration up migrate

# Run without rebuilding
docker-compose up --no-build
```

#### Production Deployment
```bash
# Build images
docker-compose build

# Run migrations first
docker-compose --profile migration up migrate

# Start services
docker-compose up -d
```

### Manual Deployment

#### Prerequisites
- Python 3.12+
- uv package manager
- System dependencies: `libsndfile1`

#### Steps
```bash
# Clone repository
git clone <repository-url>
cd openmoxie

# Install dependencies
uv sync

# Run startup script
bash start_server.sh
```

## Configuration

### Gunicorn Configuration

The Gunicorn configuration is defined in `gunicorn.conf.py`:

```python
# Key settings
bind = "0.0.0.0:8000"
workers = 1
worker_class = "gevent"
worker_connections = 10
max_requests = 1000
timeout = 30
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENMOXIE_VERSION` | `latest` | Docker image version tag |
| `DJANGO_SETTINGS_MODULE` | `openmoxie.settings` | Django settings module |

### Port Configuration

| Service | Port | Description |
|---------|------|-------------|
| Web Server | 8001 | Django application (mapped from container port 8000) |
| MQTT Broker | 8883 | MQTT over TLS |

## Health Monitoring

### Health Check Endpoint

The application provides a health check endpoint:

```bash
curl http://localhost:8001/health
# Response: {"status": "ok", "service": "openmoxie"}
```

### Logging

Gunicorn logs are configured to output to stdout/stderr for container compatibility:

- **Access logs**: HTTP request logs
- **Error logs**: Application errors and warnings
- **Django logs**: Application-specific logging (also written to files)

## Performance Tuning

### Scaling Workers

For production environments, consider adjusting the number of workers based on your server's CPU cores:

```python
# In gunicorn.conf.py
workers = multiprocessing.cpu_count() * 2 + 1
```

### Memory Considerations

Each gevent worker with 10 greenlets can handle approximately 10 concurrent connections. Monitor memory usage and adjust `worker_connections` accordingly.

### Database Connections

Ensure your database connection pool can handle the total number of potential connections:
```
Total connections = workers × worker_connections
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Find process using port 8000
   lsof -i :8000
   # Kill process if needed
   kill -9 <PID>
   ```

2. **Migration Failures**
   ```bash
   # Run migrations manually
   docker-compose --profile migration up migrate
   ```

3. **Static Files Not Loading**
   ```bash
   # Collect static files
   docker-compose exec server uv run python site/manage.py collectstatic
   ```

### Debug Mode

For debugging, you can temporarily switch back to the Django development server:

```bash
# In container
cd site
uv run python manage.py runserver 0.0.0.0:8000
```

### Logs

View application logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f server

# Real-time logs
docker-compose logs -f --tail=100 server
```

## Security Considerations

### Production Settings

Before deploying to production, ensure:

1. **Debug Mode**: Set `DEBUG = False` in Django settings
2. **Secret Key**: Use a secure, randomly generated secret key
3. **Allowed Hosts**: Configure appropriate `ALLOWED_HOSTS`
4. **HTTPS**: Configure SSL/TLS termination (recommend using a reverse proxy)
5. **Database**: Use a production database (PostgreSQL recommended)

### Reverse Proxy

Consider using nginx or similar as a reverse proxy:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoring

### Metrics

Monitor these key metrics:

- **Response Time**: Average request response time
- **Throughput**: Requests per second
- **Error Rate**: 4xx/5xx response percentages
- **Memory Usage**: Worker memory consumption
- **Connection Pool**: Database connection utilization

### Tools

Recommended monitoring tools:

- **Prometheus + Grafana**: For metrics collection and visualization
- **New Relic/DataDog**: For APM monitoring
- **Sentry**: For error tracking
- **Docker Stats**: For container resource monitoring

## Backup and Recovery

### Database Backups

Ensure regular database backups are configured:

```bash
# Example backup script
docker-compose exec server uv run python site/manage.py dumpdata > backup_$(date +%Y%m%d_%H%M%S).json
```

### Volume Persistence

Ensure the `/app/site/work` volume is properly backed up as it contains application data.
