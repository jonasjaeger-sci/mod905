make clean
cd run-full
pyretisrun -i md-full.rst -p
cd ..
cd run-100
pyretisrun -i md-100.rst -p
cd ..
cd run-100-1000
tail --lines=+1101 ../run-100/md-100-traj.txt > initial.txt
pyretisrun -i md-100-1000.rst -p
cd ..
python compare.py
