from typing import Awaitable, Callable

from aiohttp import web
from sentry_sdk import capture_exception


Handler = Callable[[web.Request], Awaitable[web.Response]]


@web.middleware
async def common_middleware(
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
