#!/bin/bash

# OpenMoxie Server Startup Script
# This script handles database migrations and starts the Gunicorn server with gevent workers

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Change to the Django project directory
cd site

print_status "Starting OpenMoxie server setup..."

# Check if we're in a uv environment
if ! command -v uv &> /dev/null; then
    print_error "uv is not installed or not in PATH"
    exit 1
fi

# Run database migrations
print_status "Running database migrations..."
uv run python manage.py migrate

# Initialize data if needed
print_status "Initializing application data..."
uv run python manage.py init_data

# Collect static files for production
print_status "Collecting static files..."
uv run python manage.py collectstatic --noinput --clear || print_warning "Static files collection failed (non-critical)"

# Start the Gunicorn server
print_status "Starting Gunicorn server with gevent workers..."
print_status "Server will be available at http://0.0.0.0:8000"
print_status "Health check available at http://0.0.0.0:8000/health"

exec uv run gunicorn \
    --config ../gunicorn.conf.py \
    --access-logfile - \
    --error-logfile - \
    openmoxie.wsgi:application
