#!/usr/bin/env bash
make clean
gmx=${1:-gmx_5.1.4_d}
echo Using gmx=$gmx
replace='s/GMXCOMMAND/'$gmx'/g'

gmxversion=$($gmx --version | grep -i "gromacs version")
echo $gmxversion

cd run-40
sed -e $replace retis.rst > retis-run.rst
pyretisrun -i retis-run.rst -p
rm retis-run.rst
cd ..

cd run-20
sed -e $replace retis.rst > retis-run.rst
pyretisrun -i retis-run.rst -p
rm retis-run.rst
cd ..

python copy_restart_files.py
cd run-restart
sed -e $replace retis.rst > retis-run.rst
pyretisrun -i retis-run.rst -p
rm retis-run.rst
cd ..

python compare.py
