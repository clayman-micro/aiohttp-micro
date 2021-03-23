import time

from aiohttp import web

from aiohttp_micro.web.middlewares import Handler


@web.middleware
async def middleware(request: web.Request, handler: Handler) -> web.Response:
    """
    Middleware to collect http requests count and response latency
    """

    start_time = time.monotonic()
    request.app["metrics"]["requests_in_progress"].labels(
        request.app["app_name"], request.path, request.method
    ).inc()

    response = await handler(request)

    resp_time = time.monotonic() - start_time
    request.app["metrics"]["requests_latency"].labels(
        request.app["app_name"], request.path
    ).observe(resp_time)
    request.app["metrics"]["requests_in_progress"].labels(
        request.app["app_name"], request.path, request.method
    ).dec()
    request.app["metrics"]["requests_total"].labels(
        request.app["app_name"], request.method, request.path, response.status
    ).inc()

    return response
