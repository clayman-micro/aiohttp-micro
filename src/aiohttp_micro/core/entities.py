from dataclasses import dataclass


@dataclass
class Entity:
    key: int


@dataclass
class Payload:
    pass


@dataclass
class Filters:
    limit: int = 10
    offset: int = 0
