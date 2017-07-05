#!/bin/bash
make clean
cd run-100
pyretisrun -i retis.rst -p
cd ..
cd run-20
pyretisrun -i retis.rst -p
cd ..
python copy_restart_files.py
cd run-load
pyretisrun -i retis.rst -p
cd ..
python compare.py
