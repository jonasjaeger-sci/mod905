tests:
	python3 -m unittest discover -v -s test/core

tests-silent:
	python3 -m unittest discover -s test/core

clean:
	find -name \*.pyc -delete
	find -name __pycache__ -delete

