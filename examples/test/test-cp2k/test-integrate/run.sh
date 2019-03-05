#!/usr/bin/env bash
set -e
make clean
pyretisrun -i cp2k.rst -p
python compare_energies.py energy.txt pyretis-cp2k-1.ener
mkdir -p cp2k-run
python make_inp.py cp2k.rst cp2k_input/cp2k-run.inp cp2k-run/cp2k.inp
cp cp2k_input/initial.xyz cp2k-run/
cd cp2k-run
cp2k -i cp2k.inp
cd ..
python compare_cp2k_energies.py pyretis-cp2k-1.ener cp2k-run/TEST-1.ener
