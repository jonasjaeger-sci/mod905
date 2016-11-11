F2PY = f2py
F2PY_FLAGS = --fcompiler=gfortran

MODULE=ljfortran

all: ${MODULE}.so

${MODULE}.so: ${MODULE}.f90
	${F2PY} ${F2PY_FLAGS} -c $< -m ${MODULE}


clean:
	find -name \*.so -delete
	find -name \*.pyc -delete
	find -name __pycache__ -delete

veryclean:
	${MAKE} clean
	find -name \*energy.dat* -delete
	find -name \*thermo.txt* -delete
	find -name \*traj.gro* -delete
