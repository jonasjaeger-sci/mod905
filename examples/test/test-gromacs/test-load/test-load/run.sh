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

cd run-20
sed -e $replace retis.rst > retis-run.rst
cp ../../../gmx/gromacs.py .
cp ../../../gmx/orderp.py .
pyretisrun -i retis-run.rst -p
pyretis_gmx_rnd_state=$(realpath rnd.state)
rm gromacs.py
rm orderp.py
rm retis-run.rst
cd ..

cp ../../gmx/copy_last_path.py .
python copy_last_path.py run-20 run-load/initial_path
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

cp ../../gmx/merge_files.py .
python merge_files.py run-20 run-load merged
cp ../../gmx/compare.py .
python compare.py run-50 merged --traj_skip --path_skip 1 2
rm merge_files.py
rm compare.py
