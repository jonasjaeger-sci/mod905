.PHONY:	
	tests
	tests-silent
	tests3
	tests-silent3
	clean
	upload-docs
	coverage

coverage:
	coverage run -m unittest discover -s test
	coverage html
 
tests:
	python -m unittest discover -v -s test

tests-silent:
	python -m unittest discover -s test

tests3:
	python3 -m unittest discover -v -s test

tests-silent3:
	python3 -m unittest discover -s test

clean:
	find -name \*.pyc -delete
	find -name \*.pyo -delete
	find -name __pycache__ -delete
	find -name \*.so -delete
	-rm bin/pyretisrun
	-rm bin/pyretisanalyse

upload-docs:
	scp -r docs/_build/html/* pyretisweb:WWW/
