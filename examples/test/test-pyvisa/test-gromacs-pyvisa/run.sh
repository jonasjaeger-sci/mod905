#!/usr/bin/env bash
set -e
cp -nr ../../test-gromacs/test-load/test-load-sparse/load-traj/* . 

pyvisa -i retis-load-rc.rst -recalculate -data ../test-gromacs-pyvisa 
pyvisa -i retis-load-rc.rst -recalculate -data pippo 

find * -not -name 'run.sh' -delete
