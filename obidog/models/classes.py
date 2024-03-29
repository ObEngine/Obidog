from pydantic import Field

from obidog.models.base import CppElement, ItemVisibility
from obidog.models.bindings import Export, LuaType
from obidog.models.flags import ObidogFlagsModel
from obidog.models.functions import (
    FunctionBaseModel,
    FunctionModel,
    FunctionUniformModel,
)
from obidog.models.location import Location
from obidog.models.qualifiers import QualifiersModel
from obidog.models.urls import URLs


class AttributeModel(CppElement):
    name: str
    namespace: str
    type: str | LuaType
    from_class: str
    qualifiers: QualifiersModel = Field(default_factory=QualifiersModel)
    description: str = ""
    initializer: str | None
    flags: ObidogFlagsModel = Field(default_factory=ObidogFlagsModel)
    export: Export = Field(default_factory=Export)
    location: Location = Field(default_factory=Location)
    visibility: ItemVisibility = ItemVisibility.Public
    _type: str = "attribute"
    urls: URLs = Field(default_factory=URLs)


class ClassBaseModel(CppElement):
    name: str


class PlaceholderClassModel(ClassBaseModel):
    pass


class ClassModel(ClassBaseModel):
    namespace: str = ""
    abstract: bool = False
    bases: list[str] = Field(default_factory=list)
    attributes: dict[str, AttributeModel] = Field(default_factory=dict)
    constructors: list[FunctionModel] = Field(default_factory=list)
    destructor: FunctionModel | None = None
    methods: dict[str, FunctionBaseModel] = Field(default_factory=dict)
    private_methods: dict[str, FunctionUniformModel] = Field(default_factory=dict)
    private_attributes: dict[str, AttributeModel] = Field(default_factory=dict)
    flags: ObidogFlagsModel = Field(default_factory=ObidogFlagsModel)
    template: bool = False
    description: str = ""
    location: Location = Field(default_factory=Location)
    export: Export = Field(default_factory=Export)
    _type: str = "class"
    urls: URLs = Field(default_factory=URLs)

    def get_bases(
        self, discard_template_types: bool = False, strip_template_types: bool = False
    ):
        if discard_template_types and strip_template_types:
            raise RuntimeError(
                "get_bases can either discard or strip template types"
                " but not the two at the same time"
            )
        if discard_template_types:
            return [base for base in self.bases if not ("<" in base and ">" in base)]
        elif strip_template_types:
            return [base.split("<")[0] for base in self.bases]
        else:
            return self.bases
