#!/usr/bin/env bash
make clean
gmx=${1:-gmx_d}
echo Using gmx=$gmx
replace='s/GMXCOMMAND/'$gmx'/g'

gmxversion=$($gmx --version | grep -i "gromacs version")
echo $gmxversion

cd run-50
sed -e $replace retis.rst > retis-run.rst
cp ../../../gmx/gromacs.py .
cp ../../../gmx/orderp.py .
pyretisrun -i retis-run.rst -p
rm retis-run.rst
rm gromacs.py
rm orderp.py
cd ..

cd run-25
sed -e $replace retis.rst > retis-run.rst
sed -e $replace retis-restart.rst > retis-restart-run.rst
cp ../../../gmx/gromacs.py .
cp ../../../gmx/orderp.py .
rm *.state
pyretisrun -i retis-run.rst -p
pyretis_gmx_rnd_state=$(realpath rnd.state)
cp $pyretis_gmx_rnd_state pyretis_gmx_rnd.state
pyretisrun -i retis-restart-run.rst -p
rm retis-run.rst
rm retis-restart-run.rst
rm gromacs.py
rm orderp.py
cd ..

cp ../../gmx/compare.py .
python compare.py run-50 run-25
rm compare.py
