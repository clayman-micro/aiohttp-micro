from typing import Any, Dict, Type

import ujson
from aiohttp import web
from marshmallow import Schema, ValidationError


async def get_payload(request: web.Request) -> Dict[str, Any]:
    if "application/json" in request.content_type:
        payload = await request.json()
    else:
        payload = await request.post()
    return dict(payload)


def json_response(data, status: int = 200, **kwargs) -> web.Response:
    return web.json_response(data, dumps=ujson.dumps, status=status, **kwargs)


def validate_payload(schema_cls: Type[Schema]):
    def wrapper(f):
        async def wrapped(request: web.Request) -> web.Response:
            payload = await get_payload(request)

            try:
                schema = schema_cls()
                document = schema.load(payload)
            except ValidationError as exc:
                return json_response({"errors": exc.messages}, status=422)

            return await f(document, request)

        return wrapped

    return wrapper
