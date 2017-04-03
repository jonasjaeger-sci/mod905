make clean
cd run-gromacs1
pyretisrun -i retis.rst -p -l DEBUG
cd ..
cd run-gromacs2
pyretisrun -i retis.rst -p -l DEBUG
cd ..
python compare.py
