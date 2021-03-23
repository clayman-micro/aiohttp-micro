from aiohttp import web

from aiohttp_micro.web.middlewares import Handler


def logging_middleware_factory(tracing_header: str = "X-B3-Traceid"):
    @web.middleware
    async def middleware(
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

    return middleware
