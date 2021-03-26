from aiohttp import web

from aiohttp_micro import AppConfig, setup as setup_micro, setup_logging, setup_metrics, setup_tracing


def init(app_name: str, cfg: AppConfig) -> web.Application:
    app = web.Application()

    setup_micro(app, app_name, cfg, package_name="aiohttp_micro")

    setup_logging(app)
    setup_metrics(app)

    if cfg.zipkin.enabled:  # type: ignore
        setup_tracing(app)

    app["logger"].info("Initialize application")

    return app
