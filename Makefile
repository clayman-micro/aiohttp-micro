.PHONY: clean clean-test clean-pyc clean-build
DOMAIN ?= micro.local
HOST ?= 0.0.0.0
PORT ?= 5000

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
	poetry run flake8 src/aiohttp_micro tests
	poetry run mypy src/aiohttp_micro tests

test:
	poetry run py.test tests

test-all:
	tox

run:
	poetry run python3 -m aiohttp_micro --debug server run --host=$(HOST) --port=$(PORT) \
    -t develop \
    -t 'traefik.enable=true' \
    -t 'traefik.http.routers.micro.rule=Host(`$(DOMAIN)`)' \
    -t 'traefik.http.routers.micro.entrypoints=web' \
    -t 'traefik.http.routers.micro.service=micro' \
    -t 'traefik.http.routers.micro.middlewares=micro-redirect@consulcatalog' \
    -t 'traefik.http.routers.micro-secure.rule=Host(`$(DOMAIN)`)' \
    -t 'traefik.http.routers.micro-secure.entrypoints=secure' \
    -t 'traefik.http.routers.micro-secure.service=micro' \
    -t 'traefik.http.routers.micro-secure.tls=true' \
    -t 'traefik.http.middlewares.micro-redirect.redirectscheme.scheme=https' \
    -t 'traefik.http.middlewares.micro-redirect.redirectscheme.permanent=true'

build: clean-build
	poetry build

release: build
	poetry publish
