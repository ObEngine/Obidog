from typing import Any

from pydantic import Field

from obidog.models.base import BaseModel, CppElement, ItemVisibility
from obidog.models.bindings import Export
from obidog.models.flags import ObidogFlagsModel
from obidog.models.location import Location
from obidog.models.qualifiers import QualifiersModel
from obidog.models.urls import URLs


class ParameterModel(BaseModel):
    name: str
    type: str
    description: str = ""
    default: Any = None
    export: Export = Field(default_factory=Export)
    ref: Any = None
    _type: str = "parameter"


class FunctionBaseModel(CppElement):
    name: str
    namespace: str
    from_class: str | None = None


class FunctionPlaceholderModel(FunctionBaseModel):
    visibility: ItemVisibility = ItemVisibility.Public


class FunctionModel(FunctionBaseModel):
    definition: str
    parameters: list[ParameterModel]
    return_type: str
    template: bool = False
    qualifiers: QualifiersModel = Field(default_factory=QualifiersModel)
    flags: ObidogFlagsModel = Field(default_factory=ObidogFlagsModel)
    force_cast: bool = False
    description: str = ""
    location: Location = Field(default_factory=Location)
    export: Export = Field(default_factory=Export)
    deleted: bool = False
    abstract: bool = False
    visibility: ItemVisibility = ItemVisibility.Public
    # FQN of proxy function
    replacement: str | None = None
    constructor: bool = False
    _type: str = "function"
    urls: URLs = Field(default_factory=URLs)


class FunctionOverloadModel(FunctionBaseModel):
    overloads: list[FunctionModel]
    flags: ObidogFlagsModel = Field(default_factory=ObidogFlagsModel)
    force_cast: bool = False
    export: Export = Field(default_factory=Export)
    _type: str = "overload"

    def to_function_model(self, base_function_model: FunctionModel) -> FunctionModel:
        return FunctionModel(
            name=self.name,
            namespace=self.namespace,
            definition=base_function_model.return_type,
            parameters=[],
            from_class=self.from_class,
            return_type=base_function_model.return_type,
        )


FunctionUniformModel = FunctionModel | FunctionOverloadModel


class FunctionPatchModel(FunctionBaseModel):
    definition: str
    parameters: list[ParameterModel]
    return_type: str
    replacement: str
    location: Location = Field(default_factory=Location)
    export: Export = Field(default_factory=Export)
