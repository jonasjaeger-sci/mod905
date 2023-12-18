#!/usr/bin/env bash
set -e
coverage run -p -m unittest discover -s test 
pycodestyle
pydocstyle --count pyretis 
python devtools/run_linting.py -i pyretis 
