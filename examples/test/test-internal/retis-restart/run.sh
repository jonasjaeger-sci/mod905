#!/usr/bin/env bash
set -e
make clean
cd retis-full
pyretisrun -i retis.rst # -p
cd ..
cd retis-10
pyretisrun -i retis.rst # -p
cd ..
cd retis-10-20
cp -r ../retis-10/0* .
pyretisrun -i retis.rst # -p
cd ..
cp ../../test-gromacs/gmx/compare.py .
python compare.py retis-10-20 retis-full --traj_skip
rm compare.py
make clean
