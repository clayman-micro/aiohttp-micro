from aiohttp import web

from aiohttp_micro import AppConfig, setup as setup_micro


def init(app_name: str, cfg: AppConfig) -> web.Application:
    app = web.Application()

    setup_micro(app, app_name, cfg, package_name="aiohttp_micro")

    app["logger"].info("Initialize application")

    return app
