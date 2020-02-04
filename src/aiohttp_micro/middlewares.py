from aiohttp import web
from sentry_sdk import capture_exception

from aiohttp_micro.handlers import Handler


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
