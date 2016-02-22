tests:
	python3 -m unittest discover -v -s test

tests-silent:
	python3 -m unittest discover -s test

clean:
	find -name \*.pyc -delete
	find -name __pycache__ -delete

