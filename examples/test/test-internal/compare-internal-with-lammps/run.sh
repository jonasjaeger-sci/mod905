#!/usr/bin/env bash
set -e
make clean
python run_md_comparison.py md-lammps.rst output_data/lammps-output.txt.gz
python run_md_comparison.py md-lammps-mix.rst output_data/lammps-output_mixture.txt.gz
make clean
