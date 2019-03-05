F2PY = f2py
F2PY_FLAGS = --fcompiler=gfortran

MODULE=ordermod

all: ${MODULE}.so

${MODULE}.so: ${MODULE}.f90
	${F2PY} ${F2PY_FLAGS} -c $< -m ${MODULE}


clean:
	find -name '*.so' -delete
	find -name '*.pyc' -delete
	find -name '*.pyo' -delete
	find -name __pycache__ -delete
	find -name 'out.rst*' -delete
	find -name '*_0*' -delete
	find -name 'pyretis.log*' -delete
	-rm -rf 0*
	-rm EXIT
	find -name '*.restart*' -delete
