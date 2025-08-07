## Moxie needs MQTT and services running on MQTT
# Use an official Python base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install Python dependencies using uv
RUN uv sync --frozen --no-cache

# Copy the current directory contents into the container at /app
COPY . /app

# Create a volume for persistent data
VOLUME /app/site/work

# Expose the Django development server port
EXPOSE 8000

# Run Gunicorn server with gevent workers using startup script
CMD ["bash", "start_server.sh"]
