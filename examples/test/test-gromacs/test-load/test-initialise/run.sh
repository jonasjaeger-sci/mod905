#!/bin/bash
make clean
cd run-25
pyretisrun -i retis.rst -p
cd ..
cd run-initialise
pyretisrun -i retis.rst -p
cd ..
python copy_restart_files.py
cd run-restart
pyretisrun -i retis.rst -p
cd ..
python compare.py
