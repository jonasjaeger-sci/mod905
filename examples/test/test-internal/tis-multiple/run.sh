#!/usr/bin/env bash
set -e
pyretisrun -i tis-multiple.rst
for x in $(seq 1 7); do 
    pyretisrun -i tis-00$x.rst
done
pyretisanalyse -i tis-multiple.rst
python compare.py
