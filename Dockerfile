# builder
FROM python:3.13-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.7.13 /uv /uvx /bin/

# Pre-compile Python bytecode and COPY packages from wheel.
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Don't try to download Python interpreter.
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

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
FROM python:3.13-slim

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
