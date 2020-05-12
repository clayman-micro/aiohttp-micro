import attr


@attr.s(slots=True, kw_only=True)
class Entity:
    key: int = attr.ib(default=0, metadata={"readonly": True})
