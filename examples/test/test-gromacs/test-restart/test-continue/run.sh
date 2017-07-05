#!/bin/bash
make clean
cd run-50
pyretisrun -i retis.rst -p
cd ..
cd run-25
pyretisrun -i retis.rst -p
pyretisrun -i retis-restart.rst -p
cd ..
python compare.py
