#!/usr/bin/env bash
set -e

basedir=$(pwd)

cd molecular_dynamics/md_movie_2d
make clean
python md_movie_2d.py
make clean
cd $basedir

cd molecular_dynamics/md_nve
make clean
python md_nve.py noplot
python md_nve_plain.py noplot
cd real_units
make clean
pyretisrun -i settings.rst
python compare.py
make clean
cd ..
make clean
cd $basedir

cd molecular_dynamics/md_nve/from_settings
pyretisrun -i settings.rst -p
make clean
cd $basedir

cd molecular_dynamics/md_nve/forward_backward
python md_forward_backward.py noplot
cd external/fortran
make clean && make
cd ..
cd cpython3
make clean && make
cd ..
python md_forward_backward_ext.py noplot
search="USE[[:space:]]=[[:space:]]'cpython3'"
new="USE='fortran'"
replace="s/"$search"/"$new"/g"
sed -e $replace md_forward_backward_ext.py > md_forward_backward_ext_tmp.py
python md_forward_backward_ext_tmp.py noplot
rm md_forward_backward_ext_tmp.py
make clean
cd ..
make clean
cd $basedir

cd molecular_dynamics/md_wca
python md_movie_2d_wca.py
cd $basedir

cd molecular_dynamics/new_integrator
python run_pendulum.py
cd $basedir

cd extending/integrator-langevin
make clean && make
pyretisrun -i retis.rst -p
make clean
cd $basedir

cd extending/integrator-vv/c
make clean && make
python md_nve.py noplot
make clean && make
pyretisrun -i settings.rst -p
make clean
cd $basedir

cd extending/integrator-vv/fortran
make clean && make
python md_nve.py noplot
make clean && make
pyretisrun -i settings.rst -p
make clean
cd $basedir

cd extending/order-parameter
pyretisrun -i retis.rst -p
make clean
cd $basedir

cd umbrella_sampling
python umbrella_sampling_mc_movie.py
python umbrella_sampling_mc.py noplot
cd $basedir
