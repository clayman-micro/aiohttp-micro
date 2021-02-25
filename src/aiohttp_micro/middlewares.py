from aiohttp import web
from sentry_sdk import capture_exception

from aiohttp_micro.handlers import Handler


LOGGER = "logger"


@web.middleware
async def catch_exceptions_middleware(
    request: web.Request, handler: Handler
) -> web.Response:
    try:
        return await handler(request)
    except Exception as exc:
        if "config" in request.app and request.app["config"].debug:
            raise exc
        else:
            capture_exception(exc)

        if isinstance(exc, (web.HTTPClientError,)):
            raise

        raise web.HTTPInternalServerError


def logging_middleware_factory(tracing_header: str = "X-B3-Traceid"):
    @web.middleware
    async def logging_middleware(
        request: web.Request, handler: Handler
    ) -> web.Response:
        request[LOGGER] = request.app[LOGGER]

        trace_id = request.headers.get(tracing_header, None)
        if trace_id:
            request[LOGGER] = request.app[LOGGER].bind(trace_id=trace_id)

        response = await handler(request)

        request[LOGGER].debug(
            f"{request.method} {request.path} {response.status}"
        )

        return response

    return logging_middleware
