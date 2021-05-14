import socket
from typing import Dict, Iterable, Optional, Union

import config
import orjson  # type: ignore
import pkg_resources
import sentry_sdk
import structlog  # type: ignore
from aiohttp.web import Application
from prometheus_client import CollectorRegistry, Counter, Enum, Gauge, Histogram, Info, Summary  # type: ignore
from sentry_sdk.integrations.aiohttp import AioHttpIntegration

from aiohttp_micro.web.handlers import meta, metrics
from aiohttp_micro.web.middlewares import common_middleware
from aiohttp_micro.web.middlewares.logging import logging_middleware_factory
from aiohttp_micro.web.middlewares.metrics import middleware as metrics_middleware
from aiohttp_micro.web.middlewares.tracing import tracing_middleware_factory


Metric = Union[Counter, Gauge, Summary, Histogram, Info, Enum]


structlog.configure(
    cache_logger_on_first_use=True,
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(serializer=orjson.dumps),
    ],
    logger_factory=structlog.BytesLoggerFactory(),
)


class ConsulConfig(config.Config):
    host = config.StrField(default="localhost", env="CONSUL_HOST")
    port = config.IntField(default=8500, env="CONSUL_PORT")
    enabled = config.BoolField(default=False, env="CONSUL_ENABLED")


class ZipkinConfig(config.Config):
    host = config.StrField(default="localhost", env="ZIPKIN_HOST")
    port = config.IntField(default=9411, env="ZIPKIN_PORT")
    enabled = config.BoolField(default=False, env="ZIPKIN_ENABLED")

    def get_address(self) -> str:
        return f"http://{self.host}:{self.port}/api/v2/spans"


class AppConfig(config.Config):
    consul = config.NestedField[ConsulConfig](ConsulConfig)
    debug = config.BoolField(default=False)
    zipkin = config.NestedField[ZipkinConfig](ZipkinConfig)
    sentry_dsn = config.StrField()


def setup(app: Application, app_name: str, config: AppConfig, package_name: Optional[str] = None) -> None:
    if not package_name:
        package_name = app_name

    app["config"] = config

    app["app_name"] = app_name
    app["hostname"] = socket.gethostname()
    app["distribution"] = pkg_resources.get_distribution(package_name)

    if config.sentry_dsn:
        dsn = str(config.sentry_dsn)
        sentry_sdk.init(
            dsn=dsn, integrations=[AioHttpIntegration()], release=app["distribution"].version,
        )

        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("app_name", app["app_name"])

    app.middlewares.append(common_middleware)  # type: ignore

    app.router.add_get("/-/health", meta.health, name="health")
    app.router.add_get("/-/meta", meta.index, name="meta")


def setup_logging(app: Application) -> None:
    app["logger"] = structlog.get_logger(
        app_name=app["app_name"], hostname=app["hostname"], version=app["distribution"].version,
    )

    app.middlewares.append(logging_middleware_factory())  # type: ignore


def setup_metrics(app: Application, extra_metrics: Dict[str, Metric] = None) -> None:
    app["metrics_registry"] = CollectorRegistry()
    app["metrics"] = {
        "requests_total": Counter(
            "requests_total",
            "Total request count",
            ("app_name", "method", "endpoint", "http_status"),
            registry=app["metrics_registry"],
        ),
        "requests_latency": Histogram(
            "requests_latency_seconds", "Request latency", ("app_name", "endpoint"), registry=app["metrics_registry"],
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

    app.middlewares.append(metrics_middleware)  # type: ignore

    app.router.add_get("/-/metrics", metrics.handler, name="metrics")


def setup_tracing(app: Application, exclude_routes: Optional[Iterable[str]] = None) -> None:
    if not exclude_routes:
        exclude_routes = []

    app.middlewares.append(  # type: ignore
        tracing_middleware_factory(exclude_routes=["metrics", *exclude_routes])
    )
