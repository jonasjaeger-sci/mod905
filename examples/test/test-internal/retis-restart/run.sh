#!/usr/bin/env bash
set -e
make clean
cd retis-full
pyretisrun -i retis.rst -p
cd ..
cd retis-100
pyretisrun -i retis.rst -p
cd ..
cd retis-100-200
cp -r ../retis-100/0* .
pyretisrun -i retis.rst -p
cd ..
python compare.py
