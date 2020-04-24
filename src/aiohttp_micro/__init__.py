import socket
from typing import Optional

import config  # type: ignore
import pkg_resources
import sentry_sdk
import structlog  # type: ignore
from aiohttp import web
from sentry_sdk.integrations.aiohttp import AioHttpIntegration

from aiohttp_micro.handlers import meta
from aiohttp_micro.middlewares import catch_exceptions_middleware


structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)


class AppConfig(config.Config):
    consul = config.NestedField(config.ConsulConfig)
    debug = config.BoolField(default=False)
    sentry_dsn = config.StrField()


def setup(
    app: web.Application,
    app_name: str,
    config: config.Config,
    package_name: Optional[str] = None,
) -> None:
    if not package_name:
        package_name = app_name

    app["config"] = config

    app["app_name"] = app_name
    app["hostname"] = socket.gethostname()
    app["distribution"] = pkg_resources.get_distribution(package_name)

    logger = structlog.get_logger()
    app["logger"] = logger.bind(
        app_name=app["app_name"],
        hostname=app["hostname"],
        version=app["distribution"].version,
    )

    if "config" in app and app["config"].sentry_dsn:
        sentry_sdk.init(
            dsn=app["config"].sentry_dsn,
            integrations=[AioHttpIntegration()],
            release=app["distribution"].version,
        )

        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("app_name", app["app_name"])

    app.middlewares.append(catch_exceptions_middleware)  # type: ignore

    app.router.add_routes(
        [
            web.get("/-/health", meta.health, name="health"),
            web.get("/-/meta", meta.index, name="index"),
        ]
    )
