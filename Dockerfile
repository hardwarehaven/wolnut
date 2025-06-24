# builder
FROM python:3.11-slim AS builder

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

COPY requirements.txt .

# Install tools needed for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

COPY . .

RUN python -m compileall -q .

# runner
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    iputils-ping \
    nut-client \
    net-tools \
    ipmitool \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy precompiled app code
COPY --from=builder /app /app

# Set correct PYTHONPATH
ENV PYTHONPATH=/app

# Run the script
CMD ["python", "-u", "wolnut/main.py"]
