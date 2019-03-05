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
	find -name \*.pyo -delete
	find -name \*out.rst* -delete
	find -name \*.restart -delete
	find -name \*.log -delete
	find -name \*.log_* -delete
	-rm -rf 0*
