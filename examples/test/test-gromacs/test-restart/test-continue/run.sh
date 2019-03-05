#!/usr/bin/env bash
make clean
gmx=${1:-gmx_d}
echo Using gmx=$gmx
replace='s/GMXCOMMAND/'$gmx'/g'

gmxversion=$($gmx --version | grep -i "gromacs version")
echo $gmxversion

cd run-50
sed -e $replace retis.rst > retis-run.rst
pyretisrun -i retis-run.rst -p
rm retis-run.rst
cd ..

cd run-25
sed -e $replace retis.rst > retis-run.rst
sed -e $replace retis-restart.rst > retis-restart-run.rst
pyretisrun -i retis-run.rst -p
pyretisrun -i retis-restart-run.rst -p
rm retis-run.rst
rm retis-restart-run.rst
cd ..

python compare.py
