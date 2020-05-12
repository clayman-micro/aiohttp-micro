import socket

import click
from aiohttp import web

from aiohttp_micro.tools.consul import Consul, Service


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
@click.option("--host", default=False, help="Specify application host")
@click.option("--port", default=5000, help="Specify application port")
@click.option(
    "--tags", "-t", multiple=True, help="Specify tags for Consul Catalog"
)
@click.pass_context
def run(ctx, host, port, tags):
    app = ctx.obj["app"]
    loop = ctx.obj["loop"]

    if not host:
        address = get_address(host)
    else:
        address = host

    try:
        port = int(port)

        if port < 1024 and port > 65535:
            raise RuntimeError("Port should be from 1024 to 65535")
    except ValueError:
        raise RuntimeError("Port should be numeric")

    service = Service(
        name=app["app_name"],
        hostname=app["hostname"],
        host=address,
        port=port,
        tags=tags,
    )

    runner = web.AppRunner(app, handle_signals=True, access_log=None)
    loop.run_until_complete(runner.setup())

    try:
        app["logger"].info(f"Application serving on {address}")

        config = app["config"]
        consul = Consul(config.consul.host, config.consul.port)
        loop.run_until_complete(consul.register(service))

        app["logger"].info(
            f"Register service {service.service_name} in Consul Catalog",
            service_name=service.service_name,
        )

        site = web.TCPSite(runner, address, port)
        loop.run_until_complete(site.start())
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        app["logger"].info(
            f"Remove service {service.service_name} from Consul Catalog",
            service_name=service.service_name,
        )

        loop.run_until_complete(consul.deregister(service))
        loop.run_until_complete(runner.cleanup())

        app["logger"].info("Shutdown application")

    loop.close()
