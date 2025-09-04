#!/bin/sh

# This script installs the `uv` tool, handling different CPU architectures.
# It's designed to be run inside a Docker container during the build process.

set -ex # Exit immediately if a command exits with a non-zero status and print commands.

apt-get update && apt-get install -y --no-install-recommends curl

case $TARGETARCH in
    "amd64")
        echo "Downloading pre-built uv for amd64..."
        curl -LsSf "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-x86_64-unknown-linux-gnu.tar.gz" -o uv.tar.gz
        tar -xvzf uv.tar.gz --strip-components 1 -C /usr/local/bin/ && chmod +x /usr/local/bin/uv && rm uv.tar.gz
        ;;
    "arm64")
        echo "Downloading pre-built uv for arm64..."
        curl -LsSf "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-aarch64-unknown-linux-gnu.tar.gz" -o uv.tar.gz
        tar -xvzf uv.tar.gz --strip-components 1 -C /usr/local/bin/ && chmod +x /usr/local/bin/uv && rm uv.tar.gz
        ;;
    *)
        echo "No pre-built binary for $TARGETARCH, installing with pip..."
        pip install uv=="${UV_VERSION}"
        ;;
esac

apt-get purge -y --auto-remove curl && apt-get clean && rm -rf /var/lib/apt/lists/*
