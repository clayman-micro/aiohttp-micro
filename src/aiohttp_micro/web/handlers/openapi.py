from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from http import HTTPStatus
from typing import Any, Collection, Dict, Iterable, Optional, Tuple, Type, Union

from aiohttp import web
from aiohttp.web_response import json_response
from marshmallow import Schema
from marshmallow.exceptions import ValidationError

from aiohttp_micro.web.handlers import get_payload


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


class InvalidParameters(Exception):
    def __init__(self, errors) -> None:
        self._errors = errors

    @property
    def errors(self):
        return self._errors


class InvalidPayload(Exception):
    def __init__(self, errors) -> None:
        self._errors = errors

    @property
    def errors(self):
        return self._errors


Tags = Iterable[str]


@dataclass
class OpenAPISpec:
    operation: str
    responses: Dict[HTTPStatus, Union[str, Type[ResponseSchema]]]
    deprecated: bool = False
    parameters: Iterable[Type[ParametersSchema]] = field(default_factory=list)
    payload: Optional[Type[PayloadSchema]] = None
    security: Optional[str] = None
    tags: Tags = field(default_factory=list)

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


Responses = Dict[HTTPStatus, Type[ResponseSchema]]
Parameters = Optional[Dict[str, Type[ParametersSchema]]]
PayloadType = Optional[Type[PayloadSchema]]


class OperationView(metaclass=ABCMeta):
    name: str
    responses: Responses
    tags: Tags

    parameters: Parameters = None
    payload_cls: PayloadType = None
    security: Optional[Any] = None

    def __init__(self, name: str, security: Any, tags: Tags) -> None:
        self.name = name
        self.security = security
        self.tags = tags

    @property
    def spec(self) -> OpenAPISpec:
        return OpenAPISpec(
            operation=self.name,
            parameters=self.parameters.values(),
            payload=self.payload_cls,
            responses=self.responses,
            security=self.security,
            tags=self.tags,
        )

    def get_parameters(self, request: web.Request) -> Dict[str, Any]:
        parameters = {}
        for section, schema_cls in self.parameters.items():
            schema = self.create_schema(schema_cls)

            if schema.in_ == ParameterIn.query:
                src = request.query
            elif schema.in_ == ParameterIn.header:
                src = request.headers
            elif schema.in_ == ParameterIn.path:
                src = request.match_info
            elif schema.in_ == ParameterIn.cookies:
                src = request.cookies

            try:
                parameters[section] = schema.load(src)
            except ValidationError as exc:
                raise InvalidParameters(errors=exc.messages)

        return parameters

    def create_schema(self, schema_cls: Type[Schema]) -> Schema:
        return schema_cls()

    async def get_payload(self, request: web.Request) -> None:
        raw_payload = await get_payload(request)

        try:
            schema = self.create_schema(self.payload_cls)
            return schema.load(raw_payload)
        except ValidationError as exc:
            raise InvalidPayload(errors=exc.errors)

    @abstractmethod
    async def process_request(
        self, request: web.Request, params: Optional[Dict[str, Any]] = None, payload: Optional[PayloadType] = None
    ) -> Union[web.Response, Tuple[Any, HTTPStatus]]:
        pass

    def process_response(self, response: Union[web.Response, Tuple[Any, HTTPStatus]]) -> web.Response:
        if not isinstance(response, web.Response):
            data, status = response

            schema_cls = self.responses.get(status, None)
            if not schema_cls:
                raise ValueError("Unsupported response status")

            schema = self.create_schema(schema_cls)
            response = json_response(schema.dump(data), status=status)

        return response

    async def handle(self, request: web.Request) -> web.Response:
        params = None
        if self.parameters:
            try:
                params = self.get_parameters(request)
            except InvalidParameters as exc:
                return self.process_response(response=(exc.errors, HTTPStatus.BAD_REQUEST))

        payload = None
        if self.payload_cls:
            try:
                payload = await self.get_payload(request)
            except InvalidPayload as exc:
                return self.process_response(response=(exc.errors, HTTPStatus.UNPROCESSABLE_ENTITY))

        response = await self.process_request(request=request, params=params, payload=payload)

        return self.process_response(response)


async def handler(request: web.Request) -> web.Response:
    """
    Expose API specification to the world
    """

    return web.json_response(request.app["spec"].to_dict())
