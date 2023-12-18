#!/usr/bin/env bash
set -e

basedir=$(pwd)
declare -a tests=(
                  "test-gromacs-pyvisa"
		  "test-gromacs-retis-pyvisa"
                  )

for i in "${tests[@]}"
do
    echo "Running in: $i"
    cd "$i"
    ./run.sh
    cd "$basedir"
done
