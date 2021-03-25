import socket
from typing import Dict, Optional, Union

import config
import pkg_resources
import sentry_sdk
import structlog  # type: ignore
from aiohttp.web import Application
from prometheus_client import (  # type: ignore
    CollectorRegistry,
    Counter,
    Enum,
    Gauge,
    Histogram,
    Info,
    Summary,
)
from sentry_sdk.integrations.aiohttp import AioHttpIntegration

from aiohttp_micro.web.handlers import meta, metrics
from aiohttp_micro.web.middlewares import common_middleware
from aiohttp_micro.web.middlewares.logging import logging_middleware_factory
from aiohttp_micro.web.middlewares.metrics import (
    middleware as metrics_middleware,
)


Metric = Union[Counter, Gauge, Summary, Histogram, Info, Enum]


structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)


class ZipkinConfig(config.Config):
    host = config.StrField(default="localhost", env="ZIPKIN_HOST")
    port = config.IntField(default=9411, env="ZIPKIN_PORT")
    enabled = config.BoolField(default=False, env="ZIPKIN_ENABLED")

    def get_address(self) -> str:
        return f"http://{self.host}:{self.port}/api/v2/spans"


class AppConfig(config.Config):
    consul = config.NestedField[config.ConsulConfig](config.ConsulConfig)
    debug = config.BoolField(default=False)
    zipkin = config.NestedField[ZipkinConfig](ZipkinConfig)
    sentry_dsn = config.StrField()


def setup(
    app: Application,
    app_name: str,
    config: config.Config,
    package_name: Optional[str] = None,
    extra_metrics: Dict[str, Metric] = None,
) -> None:
    if not package_name:
        package_name = app_name

    app["config"] = config

    app["app_name"] = app_name
    app["hostname"] = socket.gethostname()
    app["distribution"] = pkg_resources.get_distribution(package_name)

    app["metrics_registry"] = CollectorRegistry()
    app["metrics"] = {
        "requests_total": Counter(
            "requests_total",
            "Total request count",
            ("app_name", "method", "endpoint", "http_status"),
            registry=app["metrics_registry"],
        ),
        "requests_latency": Histogram(
            "requests_latency_seconds",
            "Request latency",
            ("app_name", "endpoint"),
            registry=app["metrics_registry"],
        ),
        "requests_in_progress": Gauge(
            "requests_in_progress_total",
            "Requests in progress",
            ("app_name", "endpoint", "method"),
            registry=app["metrics_registry"],
        ),
    }

    if extra_metrics:
        for key, metric in extra_metrics.items():
            app["metrics"][key] = metric
            app["metrics_registry"].register(metric)

    app["logger"] = structlog.get_logger(
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

    app.middlewares.append(common_middleware)  # type: ignore
    app.middlewares.append(metrics_middleware)  # type: ignore
    app.middlewares.append(logging_middleware_factory())  # type: ignore

    app.router.add_get("/-/health", meta.health, name="health")
    app.router.add_get("/-/meta", meta.index, name="meta")
    app.router.add_get("/-/metrics", metrics.handler, name="metrics")
