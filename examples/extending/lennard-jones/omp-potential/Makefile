F2PY = f2py
F2PY_FLAGS = --fcompiler=gfortran
F2PY_FLAGSOMP = ${F2PY_FLAGS} --f90flags='-fopenmp' -lgomp

MODULE=ljfortranp

MODULEOMP=ljfortranpomp

all: ${MODULE}.so ${MODULEOMP}.so

${MODULE}.so: ${MODULE}.f90
	${F2PY} ${F2PY_FLAGS} -c $< -m ${MODULE}

${MODULEOMP}.so: ${MODULEOMP}.f90
	${F2PY} ${F2PY_FLAGSOMP} -c $< -m ${MODULEOMP}

clean:
	find -name \*.so -delete
	find -name \*.pyc -delete
	find -name __pycache__ -delete
