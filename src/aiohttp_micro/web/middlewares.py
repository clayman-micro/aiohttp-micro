import aiozipkin
from aiohttp import web
from aiozipkin.aiohttp_helpers import _get_span
from sentry_sdk import capture_exception

from aiohttp_micro.web.handlers import Handler


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
        request["logger"] = request.app["logger"]

        trace_id = request.headers.get(tracing_header, None)
        if trace_id:
            request["logger"] = request.app["logger"].bind(trace_id=trace_id)

        response = await handler(request)

        request["logger"].debug(
            f"{request.method} {request.path} {response.status}"
        )

        return response

    return logging_middleware


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
