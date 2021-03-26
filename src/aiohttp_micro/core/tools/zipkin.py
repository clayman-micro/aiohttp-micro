import aiozipkin as az
from aiohttp import web


def create_tracer(host: str, port: int):
    async def ctx(app: web.Application):
        endpoint = az.create_endpoint(app["app_name"], ipv4=host, port=port)
        tracer = await az.create(app["config"].zipkin.get_address(), local_endpoint=endpoint, sample_rate=1.0)

        app["tracer"] = tracer

        yield

        await tracer.close()

    return ctx
