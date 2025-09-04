# --- UV Builder Stage ---
# This stage prepares the `uv` executable in a way that is compatible with all target architectures.
# It starts from a universal python base image to avoid platform-related `FROM` errors.
ARG UV_VERSION=0.7.13
FROM --platform=${TARGETPLATFORM} python:3.13-slim AS uv-builder

ARG UV_VERSION
ARG TARGETARCH # This is used by the script for logging.
COPY script/install-uv.sh /install-uv.sh
ENV UV_VERSION=${UV_VERSION}
ENV TARGETARCH=${TARGETARCH}
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/var/cache/apt \
    chmod +x /install-uv.sh && /install-uv.sh

# builder stage
FROM --platform=${TARGETPLATFORM} python:3.13-slim AS builder

# Pre-compile Python bytecode and COPY packages from wheel.
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Don't try to download Python interpreter.
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Copy the correct uv executable from our uv-builder stage
# Docker automatically selects the correct stage based on the build platform.
COPY --from=uv-builder /usr/local/bin/uv* /usr/local/bin/

# Create placeholder files to install requirements.
RUN mkdir wolnut && echo '__version__ = "0.0.0"' > wolnut/__init__.py && touch README.md

# Copy dependency files.
COPY pyproject.toml uv.lock ./

# Init environment and install dependencies.
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-install-project --no-dev

# Copy the application.
COPY . .

# Install project in .venv
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev --no-editable

# Runner
FROM --platform=${TARGETPLATFORM} python:3.13-slim AS runner

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

ENV PATH="/app/.venv/bin:$PATH"

# Install system tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    iputils-ping \
    nut-client \
    net-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder.
COPY --from=builder /app/.venv /app/.venv

# Run the script
CMD ["wolnut"]
