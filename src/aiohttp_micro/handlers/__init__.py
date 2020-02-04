from typing import Any, Awaitable, Callable, Dict

import ujson
from aiohttp import web


Handler = Callable[[web.Request], Awaitable[web.Response]]


async def get_payload(request: web.Request) -> Dict[str, Any]:
    if "application/json" in request.content_type:
        payload = await request.json()
    else:
        payload = await request.post()
    return dict(payload)


def json_response(data, status: int = 200, **kwargs) -> web.Response:
    return web.json_response(data, dumps=ujson.dumps, status=status, **kwargs)
