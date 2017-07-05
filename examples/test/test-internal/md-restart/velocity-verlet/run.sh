#!/bin/bash
make clean
cd run-full
pyretisrun -i md-full.rst -p
cd ..
cd run-100
pyretisrun -i md-100.rst -p
cd ..
cd run-100-1000
pyretisrun -i md-100-1000.rst -p
cd ..
python compare.py
