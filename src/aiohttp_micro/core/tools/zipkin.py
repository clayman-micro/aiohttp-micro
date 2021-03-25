import aiozipkin as az
from aiohttp import web
from aiozipkin.helpers import make_context


def zipkin_context(host: str, port: int):
    async def ctx(app: web.Application):
        endpoint = az.create_endpoint(app["app_name"], ipv4=host, port=port)
        tracer = await az.create(
            app["config"].zipkin.get_address(),
            local_endpoint=endpoint,
            sample_rate=1.0,
        )

        app["tracer"] = tracer

        yield

        app["logger"].info("Cleanup zipkin")

        await tracer.close()

    return ctx


def trace():
    def wrapper(f):
        async def wrapped(request: web.Request) -> web.Response:
            config = request.app["config"]

            context = make_context(request.headers)

            if context and config.zipkin.enabled:
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
                        response = await f(request)
                        child_span.tag("http.status_code", str(response.status))
                    except web.HTTPException as e:
                        child_span.tag("http.status_code", str(e.status))
                        raise

                    child_span.tag(
                        "http.response.size", response.content_length
                    )
            else:
                response = await f(request)

            return response

        return wrapped

    return wrapper
