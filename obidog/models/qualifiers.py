from obidog.models.base import BaseModel


class QualifiersModel(BaseModel):
    def __init__(
        self, const: bool = False, static: bool = False, volatile: bool = False
    ):
        self.const = const
        self.static = static
        self.volatile = volatile
