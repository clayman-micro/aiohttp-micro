from dataclasses import asdict
from enum import Enum
from typing import Any, Dict, Generic, Type, TypeVar

from marshmallow import (
    fields,
    post_dump,
    post_load,
    pre_dump,
    Schema,
    ValidationError,
)

from aiohttp_micro.entities import Entity  # noqa: F401


JSON = Dict[str, Any]


class EnumField(fields.Field):
    def __init__(self, enum_cls: Type[Enum], **kwargs) -> None:
        super().__init__(**kwargs)
        self.enum_cls = enum_cls

    def _serialize(self, value, attr, obj, **kwargs):
        if isinstance(value, self.enum_cls):
            return value.value
        return None

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            return self.enum_cls(value)
        except ValueError:
            try:
                normalized = int(value)
            except ValueError:
                raise ValidationError("Invalid value", attr, value)

            try:
                return self.enum_cls(normalized)
            except ValueError:
                raise ValidationError("Invalid value", attr, value)


ET = TypeVar("ET", bound="Entity")


class EntitySchema(Schema, Generic[ET]):
    entity_cls: Type[ET]

    key = fields.Int(data_key="id", default=0)

    @post_load
    def build_entity(self, payload: JSON, **kwargs) -> ET:
        payload.setdefault("key", 0)
        return self.entity_cls(**payload)

    @pre_dump
    def serialize_entity(self, entity: ET, **kwargs) -> JSON:
        if isinstance(entity, self.entity_cls):
            return asdict(entity)
        elif isinstance(entity, dict):
            return entity
        else:
            raise ValueError("Unserializable entity")

    @post_dump
    def cleanup(self, obj: JSON, **kwargs) -> JSON:
        drop_keys = [key for key, value in obj.items() if value is None]

        for key in drop_keys:
            del obj[key]

        return obj
