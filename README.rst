aiohttp_micro
===============

Collection of useful things for `aiohttp.web`__-based microservices.

.. _aiohttp_web: http://aiohttp.readthedocs.org/en/latest/web.html

__ aiohttp_web_


Installation
------------

    $ pip install aiohttp_micro


Usage
-----

A trivial usage example:

.. code:: python


    import click
    import config
    import uvloop
    from aiohttp import web
    from aiohttp_micro import setup as setup_micro
    from aiohttp_micro.management.server import server


    class AppConfig(config.Config):
        db = config.NestedField(config.PostgresConfig, key="db")
        debug = config.BoolField(default=False)
        sentry_dsn = config.StrField()


    def make_app(conf: config.Config, app_name: str) -> web.Application:
        app = web.Application()
        app['config'] = conf

        setup_micro(app, app_name=app_name)

        return app


    @click.group()
    @click.option("--debug", default=False)
    @click.pass_context
    def cli(ctx, debug):
        uvloop.install()

        config = AppConfig()
        config.load_from_env()

        config.debug = debug

        app = make_app("foo", config)

        ctx.obj["app"] = app
        ctx.obj["config"] = config
        ctx.obj["loop"] = loop


    cli.add_command(server, name="server")


    if __name__ == "__main__":
        cli(obj={})


Developing
----------

Run tests with::

    $ tox


License
-------

``aiohttp_micro`` is offered under the MIT license.
