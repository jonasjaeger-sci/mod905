#!/usr/bin/env bash
make clean
gmx=${1:-gmx_d}
echo Using gmx=$gmx
replace='s/GMXCOMMAND/'$gmx'/g'

gmxversion=$($gmx --version | grep -i "gromacs version")
echo $gmxversion

cd run-25
sed -e $replace retis.rst > retis-run.rst
cp ../../../gmx/gromacs.py .
cp ../../../gmx/orderp.py .
pyretisrun -i retis-run.rst -p
rm retis-run.rst
rm gromacs.py
rm orderp.py
cd ..

cd run-initialise
sed -e $replace retis.rst > retis-run.rst
cp ../../../gmx/gromacs.py .
cp ../../../gmx/orderp.py .
rm *.state
pyretisrun -i retis-run.rst -p
pyretis_gmx_rnd_state=$(realpath rnd.state)
rm retis-run.rst
rm gromacs.py
rm orderp.py
cd ..

cp ../../gmx/copy_restart_files.py .
python copy_restart_files.py run-initialise run-restart
rm copy_restart_files.py

cd run-restart
sed -e $replace retis.rst > retis-run.rst
cp ../../../gmx/gromacs.py .
cp ../../../gmx/orderp.py .
cp $pyretis_gmx_rnd_state pyretis_gmx_rnd.state
pyretisrun -i retis-run.rst -p
rm retis-run.rst
rm gromacs.py
rm orderp.py
cd ..

cp ../../gmx/compare.py .
python compare.py run-25 run-restart
rm compare.py
