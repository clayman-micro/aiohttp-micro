import asyncio

import click
import uvloop  # type: ignore
from config import EnvValueProvider, load

from aiohttp_micro import AppConfig, ConsulConfig
from aiohttp_micro.app import init
from aiohttp_micro.cli.server import server


@click.group()
@click.option("--debug", default=False, is_flag=True)
@click.pass_context
def cli(ctx, debug: bool = False) -> None:
    uvloop.install()
    loop = asyncio.get_event_loop()

    consul_config = ConsulConfig()
    load(consul_config, providers=[EnvValueProvider()])

    config = AppConfig(defaults={"consul": consul_config, "debug": debug})
    load(config, providers=[EnvValueProvider()])

    app = init("micro", config)

    ctx.obj["app"] = app
    ctx.obj["config"] = config
    ctx.obj["loop"] = loop


cli.add_command(server, name="server")


if __name__ == "__main__":
    cli(obj={})
