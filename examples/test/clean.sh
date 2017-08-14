#!/bin/sh
for filename in $(find . -type f -iname Makefile -print)
do
    dir=$(dirname "${filename}")
    make -C "${dir}" clean
done
