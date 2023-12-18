#!/usr/bin/env bash
set -e
make clean
pyretisrun -i repptis.rst -p
python compare.py
# make clean
