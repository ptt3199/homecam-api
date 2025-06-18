FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Update apt package list and install only necessary build dependencies
RUN apt-get -y update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    python3-dev \
    # OpenCV build dependencies
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libjpeg-dev \
    libpng-dev \
    libgl1-mesa-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Production stage with minimal runtime dependencies
FROM python:3.13-slim-bookworm

# Install only runtime dependencies for OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    # OpenCV runtime libraries (minimal set)
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    # JPEG/PNG support for OpenCV
    libjpeg62-turbo \
    libpng16-16 \
    # Video format support
    libavcodec59 \
    libavformat59 \
    libswscale6 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy the application and virtual environment from builder
COPY --from=builder /app /app

# Set environment variables
ENV PYTHONBUFFERED=1 \
    PYTHONWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Expose port
EXPOSE 8020

# Default command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8020"]

# Alternative: Use environment variables for more flexibility
# CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8020}"]