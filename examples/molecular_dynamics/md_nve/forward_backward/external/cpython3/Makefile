.PHONY:	
	clean

all: cextension

cextension:
	python setup.py build_ext --inplace
 
clean:
	find -name \*.so -delete
	find -name \*.pyc -delete
	find -name __pycache__ -delete
	-rm -rf build
