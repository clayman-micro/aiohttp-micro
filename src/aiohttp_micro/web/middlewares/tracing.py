from typing import List, Optional

from aiohttp import web
from aiozipkin.helpers import make_context

from aiohttp_micro.web.middlewares import Handler


def tracing_middleware_factory(exclude_routes: Optional[List[str]] = None):
    exclude: List[str] = []
    if exclude_routes:
        exclude = exclude_routes

    @web.middleware
    async def tracing_middleware(request: web.Request, handler: Handler) -> web.Response:
        context = make_context(request.headers)
        route_name = request.match_info.route.name

        if context and route_name not in exclude:
            tracer = request.app["tracer"]
            span = tracer.join_span(context)

            host = request.headers.get("Host", None)

            with tracer.new_child(span.context) as child_span:
                child_span.name(f"{request.method.upper()} {request.path}")
                child_span.kind("SERVER")

                child_span.tag("http.path", request.path)
                child_span.tag("http.method", request.method.upper())

                if host:
                    child_span.tag("http.host", host)

                try:
                    response = await handler(request)
                    child_span.tag("http.status_code", str(response.status))
                except web.HTTPException as e:
                    child_span.tag("http.status_code", str(e.status))
                    raise

                child_span.tag("http.response.size", response.content_length)
        else:
            response = await handler(request)

        return response

    return tracing_middleware
