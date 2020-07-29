from typing import List

from obidog.models.base import BaseModel
from obidog.models.flags import ObidogFlagsModel


class ParameterModel(BaseModel):
    def __init__(self, name: str, type: str, description: str = ""):
        self.name = name
        self.type = type


class FunctionQualifiersModel(BaseModel):
    def __init__(
        self, const: bool = False, static: bool = False, volatile: bool = False
    ):
        self.const = const
        self.static = static
        self.volatile = volatile


class FunctionBaseModel(BaseModel):
    def __init__(self, name: str):
        self.name = name


class FunctionModel(FunctionBaseModel):
    def __init__(
        self,
        name: str,
        definition: str,
        parameters: List[ParameterModel],
        return_type: str,
        template: bool = False,
        qualifiers: FunctionQualifiersModel = FunctionQualifiersModel(),
        flags: ObidogFlagsModel = ObidogFlagsModel(),
        description: str = "",
        location: location = "",
    ):
        super().__init__(name)
        self.definition = definition
        self.description = description
        self.parameters = parameters
        self.return_type = return_type
        self.template = template
        self.qualifiers = qualifiers
        self.flags = flags
        self.description = description
        self.location = location


class FunctionOverloadModel(FunctionBaseModel):
    def __init__(self, name: str, overloads: List[FunctionModel]):
        super().__init__(name)
        self.overloads = overloads
