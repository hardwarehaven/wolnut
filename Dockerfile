# builder
FROM python:3.11-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.7.13 /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Create placeholder files to install requirements.
RUN mkdir wolnut && echo '__version__ = "0.0.0"' > wolnut/__init__.py && touch README.md

COPY pyproject.toml uv.lock .

# Init environment and install dependencies.
RUN uv sync --locked --no-install-project --no-dev

COPY . .

# Install project in .venv
RUN uv sync --locked --no-dev --no-editable

# runner
FROM python:3.11-slim AS wolnut

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"

# Install system tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    iputils-ping \
    nut-client \
    net-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy installed script from builder
COPY --from=builder /app/.venv .venv


# Run the script
CMD ["wolnut"]
