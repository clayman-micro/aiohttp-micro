import prometheus_client  # type: ignore
from aiohttp import web


async def handler(request: web.Request) -> web.Response:
    """
    Expose application metrics to the world
    """

    resp = web.Response(body=prometheus_client.generate_latest(registry=request.app["metrics_registry"]))

    resp.content_type = prometheus_client.CONTENT_TYPE_LATEST
    return resp
