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
pyretisrun -i retis-run.rst -p
pyretis_gmx_rnd_state=$(realpath rnd.state)
rm retis-run.rst
rm gromacs.py
rm orderp.py
cd ..

cp ../../gmx/copy_last_path.py .
python copy_last_path.py run-initialise run-load/initial_path
rm copy_last_path.py
cd run-load
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
python compare.py run-25 run-load --path_skip 8
rm compare.py
