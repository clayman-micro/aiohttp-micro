import socket

import pkg_resources
import sentry_sdk
from aiohttp import web
from sentry_sdk.integrations.aiohttp import AioHttpIntegration

from aiohttp_micro.handlers import health, meta
from aiohttp_micro.middlewares import catch_exceptions_middleware


def setup(app: web.Application, app_name: str) -> None:
    app["hostname"] = socket.gethostname()
    app["distribution"] = pkg_resources.get_distribution(app_name)

    if "config" in app and app["config"].sentry_dsn:
        sentry_sdk.init(
            dsn=app["config"].sentry_dsn, integrations=[AioHttpIntegration()]
        )

    app.middlewares.append(catch_exceptions_middleware)  # type: ignore

    app.router.add_routes(
        [
            web.get("/-/health", health, name="health"),
            web.get("/-/meta", meta, name="index"),
        ]
    )
