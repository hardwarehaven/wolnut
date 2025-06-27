#!/bin/bash

# The tests should live alongside this file.
# Figure out where we are so we can let pytest know where to find the `wolnut` package.
script_dir=$(cd `dirname $0` && pwd)

# Run the tests
pytest -o pythonpath="$script_dir/../wolnut"
