#!/bin/bash

# The tests should live alongside this file.
# Figure out where we are so we can let pytest know where to find the `wolnut` package.
script_dir=$(cd `dirname $0` && pwd)

# Run tests found in this dir and let pytest know that `wolnut` is at `../`
pytest -o pythonpath="$script_dir/.."
