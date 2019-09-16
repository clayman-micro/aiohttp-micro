.PHONY: clean clean-test clean-pyc clean-build

clean: clean-build clean-pyc clean-test

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr tests/coverage
	rm -f tests/coverage.xml

install: clean
	flit install -s --python $WORKON_HOME/aiohttp_micro

lint:
	flake8 aiohttp_micro tests
	mypy aiohttp_micro tests

test:
	py.test

test-all:
	tox

build: clean-build
	python setup.py sdist
	python setup.py bdist_wheel

release: build
	twine upload dist/*
