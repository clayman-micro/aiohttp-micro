import aiozipkin
from aiohttp import web
from aiozipkin.aiohttp_helpers import _get_span

from aiohttp_micro.web.handlers import Handler


def tracing_middleware_factory(
    tracer_key: str = aiozipkin.APP_AIOZIPKIN_KEY,
    request_key: str = aiozipkin.REQUEST_AIOZIPKIN_KEY,
):
    @web.middleware
    async def tracing_middleware(
        request: web.Request, handler: Handler
    ) -> web.Response:
        tracer = request.app[tracer_key]
        span = _get_span(request, tracer)
        request[request_key] = span

        resp = await handler(request)
        return resp

    return tracing_middleware
