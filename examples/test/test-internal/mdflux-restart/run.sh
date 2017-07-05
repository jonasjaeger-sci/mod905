#!/bin/bash
make clean
cd run-full
pyretisrun -i flux.rst -p
cd ..
cd run-step1
pyretisrun -i flux.rst -p
cd ..
cd run-step2
pyretisrun -i flux.rst -p
cd ..
python compare.py
