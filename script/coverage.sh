#!/bin/bash

# This script provides a convenient way to manually generate a code coverage
# report in HTML format (coverage/index.html) before committing changes.
# It also generates coverage.xml and pytest.xml files for CI purposes.

# Find the project root directory.
if [ -z "${PROJECT_DIR}" ]; then
    export PROJECT_DIR=$(realpath `dirname "$0"`/..)
fi

echo "▶️  Running tests and generating coverage data..."

# Ensure the virtual environment is active so the `coverage` command is available.
source "${PROJECT_DIR}/script/setup_env.sh"

# Run tests with pytest-cov to generate coverage data.
# We generate the JUnit XML for test results, Cobertura XML for coverage, and a text summary.
test_output="${PROJECT_DIR}/test_output.txt"
if ! "${PROJECT_DIR}/script/tests" \
    --cov=wolnut \
    --cov-report=xml:coverage.xml \
    --cov-report=term-missing > "${test_output}" 2>&1; then
    echo "❌ Tests failed. Errors:"
    cat "${test_output}"
    rm -f "${test_output}"
    exit 1
fi

# Save the terminal report to coverage.txt and also print it to the console
cat "${test_output}" | tee coverage.txt
#rm -f "${test_output}"

if [ -z "$GITHUB_STEP_SUMMARY" ]; then
    echo "📝 Generating HTML coverage report..."
    coverage_dir="${PROJECT_DIR}/coverage/"

    # Remove an existing coverage directory to ensure a clean report.
    if [ -d "${coverage_dir}" ]; then
        rm -rf "${coverage_dir}"
        mkdir -p "${coverage_dir}"
    fi    

    # The .coverage file from the pytest run is used to generate the HTML report
    if coverage html -d "${coverage_dir}" --title="WOLNUT Code Coverage"; then
        echo "✅ HTML coverage report generated at '${coverage_dir}/index.html'."
        exit 0
    else
        echo "❌ Failed to generate HTML coverage report."
        exit 1
    fi
else
    echo "✅ Coverage XML and text summary generated for CI."
fi
