from obidog.models.base import BaseModel


class URLs(BaseModel):
    documentation: str = ""
    doxygen: str = ""
    source: str = ""
    bindings: str = ""
    example: str = ""
