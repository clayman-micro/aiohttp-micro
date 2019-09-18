import socket

import click
from aiohttp import web


def get_address(self, default: str = "127.0.0.1") -> str:
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
@click.option("--host", default="127.0.0.1", help="Specify application host")
@click.option("--port", default=5000, help="Specify application port")
@click.pass_context
def run(ctx, host, port):
    app = ctx.obj["app"]
    loop = ctx.obj["loop"]

    address = get_address(host)
    try:
        port = int(port)

        if port < 1024 and port > 65535:
            raise RuntimeError("Port should be from 1024 to 65535")
    except ValueError:
        raise RuntimeError("Port should be numeric")

    runner = web.AppRunner(app, handle_signals=True, access_log=None)

    loop.run_until_complete(runner.setup())

    try:
        site = web.TCPSite(runner, address, port)
        loop.run_until_complete(site.start())
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(runner.cleanup())

    loop.close()
