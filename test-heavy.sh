#!/usr/bin/env bash
set -e
basedir=$(pwd)

cd examples/test/test-internal/tis-multiple 
make clean
./run.sh
python compare.py
make clean
cd $basedir

cd examples/test/test-internal/retis
make clean
pyretisrun -i retis.rst -p
python compare.py
make clean
cd ../retis-load-sparse/load-frames
./run.sh
make clean
cd ../load-traj
./run.sh
make clean
cd $basedir

cd examples/test/test-gromacs/test-gromacs
make clean
./run-test1.sh gmx_d
./run-test2.sh gmx_d
make clean
cd ../test-load/test-load-sparse/load-frames
./run.sh
make clean
cd ../load-traj
./run.sh
make clean
cd $basedir

cd examples/test/test-cp2k/test-cp2k
make clean
python test_cp2k.py
make clean
cd ../test-retis-load
./run.sh
make clean
cd $basedir 
