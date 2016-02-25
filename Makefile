tests:
	python3 -m unittest discover -v -s pyretis/test

tests-silent:
	python3 -m unittest discover -s pyretis/test

clean:
	find -name \*.pyc -delete
	find -name __pycache__ -delete
	find -name \*.so -delete

