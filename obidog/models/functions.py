from typing import List

from obidog.models.base import BaseModel
from obidog.models.flags import ObidogFlagsModel
from obidog.models.qualifiers import QualifiersModel


class ParameterModel(BaseModel):
    def __init__(self, name: str, type: str, description: str = ""):
        self.name = name
        self.type = type


class FunctionBaseModel(BaseModel):
    def __init__(self, name: str):
        self.name = name


class PlaceholderFunctionModel(FunctionBaseModel):
    def __init__(self, name: str):
        super().__init__(name)


class FunctionModel(FunctionBaseModel):
    def __init__(
        self,
        name: str,
        definition: str,
        parameters: List[ParameterModel],
        return_type: str,
        template: bool = False,
        qualifiers: QualifiersModel = QualifiersModel(),
        flags: ObidogFlagsModel = ObidogFlagsModel(),
        force_cast: bool = False,
        description: str = "",
        location: str = "",
    ):
        super().__init__(name)
        self.definition = definition
        self.description = description
        self.parameters = parameters
        self.return_type = return_type
        self.template = template
        self.qualifiers = qualifiers
        self.flags = flags
        self.force_cast = force_cast
        self.description = description
        self.location = location


class FunctionOverloadModel(FunctionBaseModel):
    def __init__(self, name: str, overloads: List[FunctionModel], flags: ObidogFlagsModel = ObidogFlagsModel()):
        super().__init__(name)
        self.overloads = overloads
        self.flags = flags
