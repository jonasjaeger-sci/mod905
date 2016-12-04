.PHONY:	
	    tests
	    tests-silent
	    tests3
	    tests-silent3
	    clean
	    upload-docs

 
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

upload-docs:
	scp -r docs/_build/html/* pyretisweb:WWW/
