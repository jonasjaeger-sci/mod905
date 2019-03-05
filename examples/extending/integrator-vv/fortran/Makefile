F2PY = f2py
F2PY_FLAGS = --fcompiler=gfortran

MODULE=vvintegrator

all: ${MODULE}.so

${MODULE}.so: ${MODULE}.f90
	${F2PY} ${F2PY_FLAGS} -c $< -m ${MODULE}


clean:
	find -name \*.so -delete
	find -name \*.pyc -delete
	find -name __pycache__ -delete
	-rm thermo.txt*
	-rm traj.xyz*
	-rm energy.txt*
	-rm pyretis.log*
	-rm pyretis.restart*
	-rm out.rst*
