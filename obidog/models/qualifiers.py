from dataclasses import dataclass

from obidog.models.base import BaseModel


@dataclass
class QualifiersModel(BaseModel):
    const: bool = False
    static: bool = False
    volatile: bool = False
