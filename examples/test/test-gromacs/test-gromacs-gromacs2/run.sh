#!/usr/bin/env bash
make clean
gmx=${1:-gmx_d}
echo Using gmx=$gmx
replace='s/GMXCOMMAND/'$gmx'/g'

cd run-gromacs1
cp ../../gmx/gromacs.py .
cp ../../gmx/orderp.py .
sed -e $replace retis.rst > retis-run.rst
pyretisrun -i retis-run.rst -p -l DEBUG
rm retis-run.rst
rm gromacs.py
rm orderp.py

cd ..
cd run-gromacs2
cp ../../gmx/gromacs.py .
cp ../../gmx/orderp.py .
sed -e $replace retis.rst > retis-run.rst
pyretisrun -i retis-run.rst -p -l DEBUG
rm retis-run.rst
rm gromacs.py
rm orderp.py
cd ..

cp ../gmx/compare.py .
python compare.py run-gromacs1 run-gromacs2 --energy_skip 'vpot'
rm compare.py
