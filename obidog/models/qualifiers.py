from obidog.models.base import BaseModel


class QualifiersModel(BaseModel):
    const: bool = False
    static: bool = False
    volatile: bool = False
