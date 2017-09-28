#!/bin/bash
make clean
gmx=${1:-gmx_d}
echo Using gmx=$gmx
replace='s/GMXCOMMAND/'$gmx'/g'

cd run-gromacs1
sed -e $replace retis.rst > retis-run.rst
pyretisrun -i retis-run.rst -p -l DEBUG
rm retis-run.rst

cd ..
cd run-gromacs2
sed -e $replace retis.rst > retis-run.rst
pyretisrun -i retis-run.rst -p -l DEBUG
rm retis-run.rst
cd ..
python compare.py
