#!/usr/bin/env bash
set -e
basedir=$(pwd)

cd examples/test/test-internal/
./run-all-internal.sh
cd $basedir

cd examples/test/test-gromacs/
./run-all-gromacs.sh
cd $basedir

cd examples/test/test-cp2k/
./run-all-cp2k.sh
cd $basedir 
