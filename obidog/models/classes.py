from dataclasses import dataclass, field
from typing import List, Dict

from obidog.models.base import BaseModel, ItemVisibility
from obidog.models.bindings import Export
from obidog.models.flags import ObidogFlagsModel
from obidog.models.functions import FunctionModel
from obidog.models.location import Location
from obidog.models.qualifiers import QualifiersModel
from obidog.models.urls import URLs


@dataclass
class AttributeModel(BaseModel):
    name: str
    namespace: str
    type: str
    qualifiers: QualifiersModel = QualifiersModel()
    description: str = ""
    initializer: str = ""
    flags: ObidogFlagsModel = ObidogFlagsModel()
    export: Export = Export()
    location: Location = field(default_factory=lambda: Location())
    visibility: ItemVisibility = ItemVisibility.Public
    _type: str = "attribute"
    urls: URLs = field(default_factory=lambda: URLs())


@dataclass
class ClassBaseModel(BaseModel):
    name: str


@dataclass
class PlaceholderClassModel(ClassBaseModel):
    pass


@dataclass
class ClassModel(ClassBaseModel):
    namespace: str = ""
    abstract: bool = False
    bases: List[str] = None
    attributes: Dict[str, AttributeModel] = None
    constructors: List[FunctionModel] = None
    destructor: FunctionModel = None
    methods: Dict[str, FunctionModel] = None
    private_methods: Dict[str, FunctionModel] = None
    private_attributes: Dict[str, AttributeModel] = None
    flags: ObidogFlagsModel = ObidogFlagsModel()
    template: bool = False
    description: str = ""
    location: Location = field(default_factory=lambda: Location())
    export: Export = Export()
    _type: str = "class"
    urls: URLs = field(default_factory=lambda: URLs())

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
