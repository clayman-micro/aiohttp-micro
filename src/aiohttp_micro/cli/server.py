import socket

import click
from aiohttp import web

from aiohttp_micro.core.tools.consul import register, Service
from aiohttp_micro.core.tools.zipkin import create_tracer


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
@click.option("--tags", "-t", multiple=True, help="Specify tags for Consul Catalog")
@click.pass_context
def run(ctx, host, port, tags):
    app = ctx.obj["app"]

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

    if app["config"].consul.enabled:
        consul_service = Service(name=app["app_name"], hostname=app["hostname"], host=address, port=port, tags=tags)
        app.cleanup_ctx.append(register(consul_service))

    app.cleanup_ctx.append(create_tracer(host, port))

    app["logger"].info(f"Application serving on http://{address}:{port}")

    web.run_app(app, host=host, port=port, print=None)

    app["logger"].info("Shutdown application")
