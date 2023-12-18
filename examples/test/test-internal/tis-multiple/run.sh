#!/usr/bin/env bash
set -e
make clean
pyretisrun -i tis-multiple.rst
for x in $(seq 1 3); do 
    pyretisrun -i "tis-00$x.rst"
done
pyretisanalyse -i tis-multiple.rst
python compare.py
make clean
