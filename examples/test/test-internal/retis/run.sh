#!/bin/bash
make clean
pyretisrun -i retis.rst -p
python compare.py
