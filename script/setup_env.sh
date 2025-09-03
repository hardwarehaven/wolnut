#!/bin/bash

# This script sets up the Python virtual environment for the project.
# It creates the venv if it doesn't exist, activates it, and installs dependencies.
# This script is intended to be sourced by other scripts.

set -e # Exit immediately if a command exits with a non-zero status.

# Find and move to the project root directory.
# Find the project root directory.
if [ -z "${PROJECT_DIR}" ]; then
    export PROJECT_DIR=$(realpath `dirname "$0"`/..)
fi
cd "${PROJECT_DIR}"

if [ -n "${VIRTUAL_ENV}" ] && [ -d "${VIRTUAL_ENV}" ]; then
    echo "🐍 Virtual environment already active at '${VIRTUAL_ENV}'."
else
    # Define a virtual environment path if not already set.
    if [ -z "${VIRTUAL_ENV}" ]; then
        export VIRTUAL_ENV="${PROJECT_DIR}/.venv"
    fi

    # Create the virtual environment if it doesn't exist.
    if [ ! -d "${VIRTUAL_ENV}" ]; then
        echo "🐍 Creating Python virtual environment in '${VIRTUAL_ENV}'..."
        uv venv .venv
    fi

    # Activate the virtual environment.
    source "${VIRTUAL_ENV}/bin/activate"

    echo "🐍 Syncing uv..."
    uv sync --dev

fi