## OpenMoxie Docker Build
# Use multi-stage builds to create a final image without uv

# Builder stage - install dependencies with uv
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Disable Python downloads to use the system interpreter across both images
ENV UV_PYTHON_DOWNLOADS=0

# Set the working directory in the container
WORKDIR /app

# Install dependencies using lockfile
COPY pyproject.toml uv.lock /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev

# Copy the source code
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Final stage - clean image without uv
FROM python:3.12-slim-bookworm

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the application and virtual environment from the builder
COPY --from=builder /app /app

# Create a volume for persistent data
VOLUME /app/site/work

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Expose the Django development server port
EXPOSE 8000

# Ensure permissions for site/work directory
RUN mkdir -p /app/site/work && chmod -R 777 /app/site/work

# Run Gunicorn server with gevent workers using startup script
CMD ["bash", "start_server.sh"]
