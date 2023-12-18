#!/usr/bin/env bash
set -e
make clean
python test_cp2k.py
make clean
