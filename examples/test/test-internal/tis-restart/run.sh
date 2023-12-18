#!/usr/bin/env bash
set -e
make clean
cd run-full
pyretisrun -i tis-001.rst # -p
pyretisanalyse -i tis-001.rst # -p
cd ..
cd run-10
pyretisrun -i tis-001.rst # -p
cd ..
cd run-10-20
cp -r ../run-10/001 .
pyretisrun -i tis-001.rst # -p
cd ..
python compare.py 
make clean
