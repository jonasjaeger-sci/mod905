#!/usr/bin/env bash
set -e
coverage run -m unittest discover -s test 
pycodestyle --filename=*.py --count --statistics --exclude=./docs 
pydocstyle --count pyretis 
python devtools/run_linting.py pyretis 
