from dataclasses import dataclass, field
from enum import Enum
from http import HTTPStatus
from typing import Collection, Dict, Iterable, Optional, Type, Union

from aiohttp import web
from marshmallow import Schema


class ParameterIn(Enum):
    cookies = "cookies"
    header = "header"
    path = "path"
    query = "query"


class PayloadSchema(Schema):
    pass


class ParametersSchema(Schema):
    in_ = ParameterIn.path


class ResponseSchema(Schema):
    pass


@dataclass
class OpenAPISpec:
    operation: str
    responses: Dict[HTTPStatus, Union[str, Type[ResponseSchema]]]
    deprecated: bool = False
    parameters: Iterable[Type[ParametersSchema]] = field(default_factory=list)
    payload: Optional[Type[PayloadSchema]] = None
    security: Optional[str] = None
    tags: Iterable[str] = field(default_factory=list)

    def _generate_responses(self) -> Dict[str, Dict[str, Collection[str]]]:
        responses = {}

        for status_code, schema in self.responses.items():
            response = None

            if isinstance(schema, str):
                response = {"description": schema, "content": {"text/plain": {"schema": {"type": "string"}}}}
            elif issubclass(schema, ResponseSchema):
                response = {
                    "content": {"application/json": {"schema": schema}},
                }

                if schema.__doc__:
                    response["description"] = schema.__doc__
            else:
                raise ValueError(f"Unknown response type: {schema}")

            if response:
                responses[str(status_code.value)] = response

        return responses

    def generate(self) -> Dict[str, str]:
        operation = {
            "operationId": self.operation,
            "responses": self._generate_responses(),
        }

        if self.deprecated:
            operation["deprecated"] = self.deprecated

        if self.parameters:
            operation["parameters"] = [{"in": schema.in_.value, "schema": schema} for schema in self.parameters]

        if self.payload:
            operation["requestBody"] = {
                "description": self.payload.__doc__,
                "content": {"application/json": {"schema": self.payload}},
                "required": True,
            }

        if self.security:
            operation["security"] = [{self.security: []}]

        if self.tags:
            operation["tags"] = self.tags

        return operation


async def handler(request: web.Request) -> web.Response:
    """
    Expose API specification to the world
    """

    return web.json_response(request.app["spec"].to_dict())
