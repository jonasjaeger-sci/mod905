tests:
	python -m unittest discover test/core

clean:
	find -name \*.pyc -delete
	find -name __pycache__ -delete

