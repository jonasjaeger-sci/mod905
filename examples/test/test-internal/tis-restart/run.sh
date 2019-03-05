#!/usr/bin/env bash
make clean
cd run-full
pyretisrun -i tis-001.rst -p
cd ..
cd run-100
pyretisrun -i tis-001.rst -p
cd ..
cd run-100-200
cp -r ../run-100/001 .
pyretisrun -i tis-001.rst -p
cd ..
python compare.py
