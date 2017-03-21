make clean
cd retis-full
pyretisrun -i retis.rst -p
cd ..
cd retis-100
pyretisrun -i retis.rst -p
cd ..
python copy_restart_files.py
cd retis-100-200
pyretisrun -i retis.rst -p
cd ..
python compare.py
