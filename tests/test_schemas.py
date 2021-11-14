from dataclasses import dataclass
from enum import Enum

import pytest  # type: ignore
from marshmallow import fields, Schema, ValidationError

from aiohttp_micro.core.entities import Entity
from aiohttp_micro.core.schemas import EntitySchema, EnumField


class Status(Enum):
    inactive = 0
    active = 1


@pytest.fixture(scope="function")
def schema():
    class TestSchema(Schema):
        status = EnumField(Status)

    return TestSchema()


@pytest.mark.unit
@pytest.mark.parametrize("status", (1, "1"))
def test_load_enum_field(schema, status):
    document = schema.load({"status": status})  # act

    assert document["status"] == Status.active


@pytest.mark.unit
@pytest.mark.parametrize("status", ("2", 2, "foo", None))
def test_load_enum_failed(schema, status):
    with pytest.raises(ValidationError):
        schema.load({"status": status})


@dataclass
class Tag(Entity):
    name: str


@pytest.fixture(scope="function")
def tag_schema():
    class TagSchema(EntitySchema):
        entity_cls = Tag

        name = fields.Str()

    return TagSchema()


@pytest.mark.unit
def test_load_entity(tag_schema):
    tag = tag_schema.load({"name": "Food"})  # act

    assert tag == Tag(key=0, name="Food")


@pytest.mark.unit
def test_serialize_entity(tag_schema):
    tag = Tag(key=1, name="Food")

    serialized = tag_schema.dump(tag)  # act

    assert serialized == {"id": 1, "name": "Food"}
