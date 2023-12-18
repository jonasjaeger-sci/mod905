#!/usr/bin/env bash
set -e
cp ../Makefile .
make clean
cd run-full
pyretisrun -i md-full.rst #-p
cd ..
cd run-10
pyretisrun -i md-10.rst #-p
cd ..
cd run-10-100
pyretisrun -i md-10-100.rst # -p
cd ..
cp ../compare.py .
python compare.py
make clean
rm compare.py
rm Makefile
