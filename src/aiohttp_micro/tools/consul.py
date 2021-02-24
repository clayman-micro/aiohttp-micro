from dataclasses import dataclass, field
from typing import Dict, List

import ujson
from aiohttp import ClientSession

from aiohttp_micro.middlewares import LOGGER


@dataclass
class Service:
    name: str
    hostname: str
    host: str = "127.0.0.1"
    port: int = 5000
    tags: List[str] = field(default_factory=list)

    @property
    def service_name(self) -> str:
        return f"{self.name}_{self.hostname}"

    @property
    def healthcheck(self) -> Dict[str, str]:
        return {
            "HTTP": f"http://{self.host}:{self.port}/-/health",
            "Interval": "10s",
        }


class Consul:
    __slots__ = ("_host", "_port")

    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port

    async def register(self, service: Service) -> bool:
        payload = {
            "ID": service.service_name,
            "Name": service.name,
            "Address": service.host,
            "Port": service.port,
            "Tags": service.tags,
            "Checks": [service.healthcheck],
        }

        url = f"http://{self._host}:{self._port}/v1/agent/service/register"

        done = False
        async with ClientSession() as session:
            async with session.put(url, data=ujson.dumps(payload)) as resp:
                done = resp.status == 200

        return done

    async def deregister(self, service: Service) -> bool:
        url = "http://{host}:{port}/v1/agent/service/deregister/{id}".format(
            host=self._host, port=self._port, id=service.service_name
        )

        done = False
        async with ClientSession() as session:
            async with session.put(url) as resp:
                done = resp.status == 200

        return done


def register(service: Service):
    async def ctx(app):
        config = app["config"]

        consul = Consul(config.consul.host, config.consul.port)

        await consul.register(service)

        app[LOGGER].info(
            f"Register service {service.service_name} in Consul Catalog"
        )

        yield

        await consul.deregister(service)

        app[LOGGER].info(
            f"Remove service {service.service_name} from Consul Catalog"
        )

    return ctx
