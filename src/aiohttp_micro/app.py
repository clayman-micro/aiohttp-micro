from aiohttp import web
from apispec import APISpec  # type: ignore
from apispec.ext.marshmallow import MarshmallowPlugin  # type: ignore

from aiohttp_micro import AppConfig, setup as setup_micro
from aiohttp_micro.handlers import openapi


def init(app_name: str, cfg: AppConfig) -> web.Application:
    app = web.Application()

    setup_micro(app, app_name, cfg, package_name="aiohttp_micro")

    app["spec"] = APISpec(
        title="Micro API",
        version=app["distribution"].version,
        openapi_version="3.0.2",
        info={"description": "Micro service API"},
        plugins=[MarshmallowPlugin()],
    )

    app.router.add_get("/api/spec.json", openapi.spec, name="api.spec")

    for route in app.router.routes():
        if route.method.lower() == "head":
            continue

        if hasattr(route.handler, "spec") and route.resource:
            operation_spec = route.handler.spec["operation"]  # type: ignore
            app["spec"].path(
                path=route.resource.canonical,
                operations={route.method.lower(): operation_spec},
            )

    app["logger"].info("Initialize application")

    return app
