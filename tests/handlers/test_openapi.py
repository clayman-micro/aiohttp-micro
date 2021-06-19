from http import HTTPStatus

from marshmallow import fields, Schema

from aiohttp_micro.web.handlers.openapi import OpenAPISpec, ParameterIn, ParametersSchema, PayloadSchema, ResponseSchema


def test_simple_operation():
    spec = OpenAPISpec(operation="testOperation", responses={HTTPStatus.OK: "Plain text response"}, tags=["test"])

    operation = spec.generate()

    assert operation == {
        "operationId": "testOperation",
        "responses": {
            "200": {"description": "Plain text response", "content": {"text/plain": {"schema": {"type": "string"}}}}
        },
        "tags": ["test"],
    }


class ItemSchema(Schema):
    key = fields.Int(data_key="id", description="Item id")
    name = fields.Str(description="Item name")


class CollectionFilters(ParametersSchema):
    in_ = ParameterIn.query

    offset = fields.Int(default=0, missing=0, data_key="OFFSET", description="Offset from collection beginning")
    limit = fields.Int(default=10, missing=10, description="Number of items per page")


class CollectionResponseSchema(ResponseSchema):
    """Collection response"""

    items = fields.List(fields.Nested(ItemSchema), description="Collection of items")


class AddItemPayloadSchema(PayloadSchema):
    """Add new item"""

    name = fields.Str(description="Item name")


class ItemResponseSchema(ResponseSchema):
    """Item response"""

    item = fields.Nested(ItemSchema, data_key="id", description="Item")


def test_simple_json_operation():
    spec = OpenAPISpec(operation="fetchCollection", responses={HTTPStatus.OK: CollectionResponseSchema})

    operation = spec.generate()

    assert operation == {
        "operationId": "fetchCollection",
        "responses": {
            "200": {
                "description": "Collection response",
                "content": {"application/json": {"schema": CollectionResponseSchema}},
            }
        },
    }


def test_simple_json_operation_with_params():
    spec = OpenAPISpec(
        operation="fetchCollection", parameters=[CollectionFilters], responses={HTTPStatus.OK: CollectionResponseSchema}
    )

    operation = spec.generate()

    assert operation == {
        "operationId": "fetchCollection",
        "parameters": [{"in": "query", "schema": CollectionFilters}],
        "responses": {
            "200": {
                "description": "Collection response",
                "content": {"application/json": {"schema": CollectionResponseSchema}},
            }
        },
    }


def test_simple_operation_with_payload():
    spec = OpenAPISpec(
        operation="addItem", payload=AddItemPayloadSchema, responses={HTTPStatus.CREATED: ItemResponseSchema}
    )

    operation = spec.generate()

    assert operation == {
        "operationId": "addItem",
        "requestBody": {
            "description": AddItemPayloadSchema.__doc__,
            "content": {"application/json": {"schema": AddItemPayloadSchema}},
            "required": True,
        },
        "responses": {
            "201": {"description": "Item response", "content": {"application/json": {"schema": ItemResponseSchema}}}
        },
    }
