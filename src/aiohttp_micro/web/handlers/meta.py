from aiohttp import web

from aiohttp_micro.core.tools.zipkin import trace
from aiohttp_micro.web.handlers import json_response


@trace()
async def index(request: web.Request) -> web.Response:
    return json_response(
        {
            "hostname": request.app["hostname"],
            "project": request.app["distribution"].project_name,
            "version": request.app["distribution"].version,
        }
    )


@trace()
async def health(request: web.Request) -> web.Response:
    return web.Response(body=b"Healthy")
