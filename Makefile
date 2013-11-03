test:
	nosetests --verbose

upload:
	python setup.py sdist upload

clean:
	find . -iname '*.pyc' -exec rm {} \;
