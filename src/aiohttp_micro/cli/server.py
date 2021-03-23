import asyncio
import socket

# import aiozipkin
import click
from aiohttp import web

from aiohttp_micro.core.tools.consul import register, Service

# from aiohttp_micro.web.middlewares import tracing_middleware_factory


def get_address(default: str = "127.0.0.1") -> str:
    try:
        ip_address = socket.gethostbyname(socket.gethostname())
    except socket.gaierror:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 1))
            ip_address = s.getsockname()[0]
        except socket.gaierror:
            ip_address = default
        finally:
            s.close()

    return ip_address


@click.group()
@click.pass_context
def server(ctx):
    pass


@server.command()
@click.option("--host", default=None, help="Specify application host")
@click.option("--port", default=5000, help="Specify application port")
@click.option(
    "--tags", "-t", multiple=True, help="Specify tags for Consul Catalog"
)
@click.pass_context
def run(ctx, host, port, tags):
    app = ctx.obj["app"]
    # loop = asyncio.get_event_loop()

    try:
        port = int(port)

        if port < 1024 and port > 65535:
            raise RuntimeError("Port should be from 1024 to 65535")
    except ValueError:
        raise RuntimeError("Port should be numeric")

    if not host:
        host = "127.0.0.1"
        address = "127.0.0.1"
    else:
        address = get_address()

    app.cleanup_ctx.append(
        register(
            Service(
                name=app["app_name"],
                hostname=app["hostname"],
                host=address,
                port=port,
                tags=tags,
            )
        )
    )

    app["logger"].info(f"Application serving on http://{address}:{port}")

    # endpoint = aiozipkin.create_endpoint(
    #     app["app_name"], ipv4=address, port=port
    # )
    # tracer = loop.run_until_complete(
    #     aiozipkin.create(
    #         app["config"].zipkin.get_address(), endpoint, sample_rate=1.0,
    #     )
    # )

    # app[aiozipkin.APP_AIOZIPKIN_KEY] = tracer

    # async def close_aiozipkin(app: web.Application) -> None:
    #     await app[aiozipkin.APP_AIOZIPKIN_KEY].close()

    # app.on_cleanup.append(close_aiozipkin)

    # app.middlewares.append(tracing_middleware_factory())

    # aiozipkin.setup(app, tracer)

    web.run_app(app, host=host, port=port, print=None)

    app["logger"].info("Shutdown application")
