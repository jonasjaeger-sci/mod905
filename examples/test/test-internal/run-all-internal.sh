#!/usr/bin/env bash
set -e

basedir=$(pwd)

declare -a tests=("compare-internal-with-lammps"
                  "mdflux-restart/version1"
                  "mdflux-restart/version2"
                  "md-restart/velocity-verlet"
                  "md-restart/langevin"
                  "retis"
                  "retis-restart"
                  "tis-multiple"
                  "tis-restart"
                  )

for i in "${tests[@]}"
do
    echo "Running in: $i"
    cd $i
    ./run.sh
    cd $basedir
done

