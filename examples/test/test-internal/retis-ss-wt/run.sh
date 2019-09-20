#!/usr/bin/env bash
set -e
make clean

folders=('sh' 'ss' 'ss-ha' 'wt' 'ss+wt' 'ss+wt-ha')
moves=("'sh','sh','sh','sh'" "'sh','ss','ss','sh'"
       "'sh','ss','ss','sh'" "'sh','sh','wt','sh'"
       "'sh','ss','ss','wt'" "'sh','ss','ss','wt'")
for i_f in {0..5}; do
   mkdir -p ${folders[$i_f]}
   cd ${folders[$i_f]}
   cp ../initial.xyz .
   cp ../retis.rst .
   sed -i "s/'sh', 'sh', 'sh', 'sh'/${moves[$i_f]}/g" retis.rst
   if [ ${folders[$i_f]} = 'ss-ha' ]; then
       sed -i "s/high_accept = False/high_accept = True/g" retis.rst
   fi
   pyretisrun -i retis.rst -p
   pyretisanalyse -i retis.rst 
   cd ..
done
#python compare.py
