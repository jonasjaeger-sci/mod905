#!/usr/bin/env bash
set -e
make clean
gmx=${1:-gmx_d}
echo "Using gmx=$gmx"
replace="s/GMXCOMMAND/$gmx/g"

sed -e $replace repptis.rst > repptis-run.rst
cp ../gmx/gromacs.py .
cp ../gmx/orderp.py .
pyretisrun -i repptis-run.rst -l DEBUG
python compare.py
rm repptis-run.rst
rm gromacs.py
rm orderp.py

make clean
