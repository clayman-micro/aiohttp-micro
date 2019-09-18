from typing import NamedTuple

import pkg_resources  # type: ignore
import pytest  # type: ignore
from aiohttp import web

from aiohttp_micro import setup


@pytest.fixture(scope="function")
def distribution(monkeypatch):
    class Distribution(NamedTuple):
        project_name: str
        version: str

    def patch_distribution(*args, **kwargs):
        return Distribution("foo", "0.0.1.dev1")

    monkeypatch.setattr(pkg_resources, "get_distribution", patch_distribution)


@pytest.yield_fixture(scope="function")
def app(loop, distribution):
    app = web.Application()
    setup(app, app_name="foo")

    runner = web.AppRunner(app)
    loop.run_until_complete(runner.setup())

    yield app

    loop.run_until_complete(runner.cleanup())
