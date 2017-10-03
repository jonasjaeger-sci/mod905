#!/bin/bash
make clean
gmx=${1:-gmx_5.1.4_d}
echo Using gmx=$gmx
replace='s/GMXCOMMAND/'$gmx'/g'

cd gromacs1
sed -e $replace retis.rst > retis-run.rst
pyretisrun -i retis-run.rst -p -l DEBUG
rm retis-run.rst

cd ..
cd gromacs2
sed -e $replace retis.rst > retis-run.rst
pyretisrun -i retis-run.rst -p -l DEBUG
rm retis-run.rst
cd ..

gmxversion=$($gmx --version | grep -i "gromacs version")
python compare.py "$gmxversion"
