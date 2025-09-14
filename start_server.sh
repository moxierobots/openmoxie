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

# Ensure we're using the virtual environment from the build
export PATH="venv/bin:$PATH"

# Ensure site/work directory exists and has proper permissions
if [ ! -d "work" ]; then
    print_status "Creating work directory..."
    mkdir -p work
fi
chmod -R 777 work

# Run database migrations
print_status "Running database migrations..."
python manage.py migrate || {
    print_error "Database migration failed. This might be a permissions issue."
    # Try to fix permissions
    find ../site -type d -exec chmod 755 {} \;
    find ../site -type f -exec chmod 644 {} \;
    # Try again
    print_status "Retrying migrations..."
    python manage.py migrate
}

# Initialize data if needed
print_status "Initializing application data..."
python manage.py init_data

# Collect static files for production
print_status "Collecting static files..."

# Use the STATIC_ROOT from environment if set, otherwise use default
if [ ! -z "$STATIC_ROOT" ]; then
    print_status "Using STATIC_ROOT: $STATIC_ROOT"
    # Ensure the parent directory exists
    STATIC_DIR=$(dirname "$STATIC_ROOT")
    if [ ! -d "$STATIC_DIR" ]; then
        print_status "Creating parent directory: $STATIC_DIR"
        mkdir -p "$STATIC_DIR"
    fi
    # Ensure the static directory exists
    mkdir -p "$STATIC_ROOT"
    # Set appropriate permissions
    chmod -R 755 "$STATIC_ROOT" 2>/dev/null || true
else
    # Default static root location
    DEFAULT_STATIC_ROOT="site/static"
    print_status "No STATIC_ROOT set, using default: $DEFAULT_STATIC_ROOT"
    mkdir -p "$DEFAULT_STATIC_ROOT"
    chmod -R 755 "$DEFAULT_STATIC_ROOT" 2>/dev/null || true
fi

# Run collectstatic with better error handling
print_status "Running collectstatic command..."
python manage.py collectstatic --noinput --clear 2>&1 | while IFS= read -r line; do
    if [[ "$line" == *"error"* ]] || [[ "$line" == *"Error"* ]]; then
        print_error "$line"
    elif [[ "$line" == *"warning"* ]] || [[ "$line" == *"Warning"* ]]; then
        print_warning "$line"
    else
        echo "$line"
    fi
done

# Check if static files were collected successfully
if [ $? -eq 0 ]; then
    print_status "Static files collected successfully"
else
    print_warning "Static files collection completed with warnings"
fi

# Start the Gunicorn server
print_status "Starting Gunicorn server with gevent workers..."
print_status "Server will be available at http://0.0.0.0:8000"
print_status "Health check available at http://0.0.0.0:8000/health"

# Ensure log directory exists with proper permissions
if [ ! -d "work/logs" ]; then
    print_status "Creating logs directory..."
    mkdir -p work/logs
    chmod -R 777 work/logs
fi

exec gunicorn \
    --config ../gunicorn.conf.py \
    --access-logfile - \
    --error-logfile - \
    openmoxie.wsgi:application
