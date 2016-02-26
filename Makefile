tests:
	python3 -m unittest discover -v -s test

tests-silent:
	python3 -m unittest discover -s test

tests2:
	python2.7 -m unittest discover -v -s test

tests-silent2:
	python2.7 -m unittest discover -s test

clean:
	find -name \*.pyc -delete
	find -name __pycache__ -delete
	find -name \*.so -delete

