from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Dict, Optional, Tuple, Union

from aiohttp import web
from aiohttp.hdrs import METH_GET
from marshmallow import fields

from aiohttp_micro import AppConfig
from aiohttp_micro import setup as setup_micro
from aiohttp_micro import setup_logging, setup_metrics, setup_openapi, setup_tracing
from aiohttp_micro.core.entities import Entity
from aiohttp_micro.core.schemas import EntitySchema
from aiohttp_micro.web.handlers.openapi import OperationView, ResponseSchema
from aiohttp_micro.web.schemas import CollectionFiltersSchema, CommonParameters


@dataclass
class Item(Entity):
    name: str


class ItemSchema(EntitySchema):
    """Item."""

    entity_cls = Item

    key = fields.Int(required=True, data_key="id", dump_only=True, description="Item id")
    name = fields.Str(required=True, description="Item name")


class GetItemsResponseSchema(ResponseSchema):
    """Items list."""

    items = fields.List(fields.Nested(ItemSchema), required=True, description="Items")


class GetItemsView(OperationView):
    """Get items list."""

    parameters = {"common": CommonParameters, "filters": CollectionFiltersSchema}

    responses = {
        HTTPStatus.OK: GetItemsResponseSchema,
    }

    async def process_request(
        self, request: web.Request, params: Optional[Dict[str, Any]], **kwargs
    ) -> Union[web.Response, Tuple[Any, HTTPStatus]]:
        app: web.Application = request.app
        app["logger"].info("Fetch items with filters", filters=params["filters"])

        return {"items": [Item(key=1, name="Foo")]}, HTTPStatus.OK


def init(app_name: str, cfg: AppConfig) -> web.Application:
    app = web.Application()

    setup_micro(app, app_name, cfg, package_name="aiohttp_micro")

    setup_logging(app)
    setup_metrics(app)

    if cfg.zipkin.enabled:  # type: ignore
        setup_tracing(app)

    setup_openapi(
        app,
        title="Micro",
        version=app["distribution"].version,
        description="Demo microservice",
        operations=[
            # Account operations
            (METH_GET, "/api/items", GetItemsView(name="getItems", security="TokenAuth", tags=["items"]),),
        ],
        security=("TokenAuth", {"type": "apiKey", "name": "X-Access-Token", "in": "header"}),
    )

    app["logger"].info("Initialize application")

    return app
