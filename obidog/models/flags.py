from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from obidog.models.base import BaseModel


class MetaTag(Enum):
    NonCopyable = "NonCopyable"


@dataclass
class ObidogFlagsModel(BaseModel):
    helpers: List[str] = field(default_factory=lambda: [])
    template_hints: Dict[str, List[str]] = field(default_factory=lambda: {})
    nobind: bool = False
    additional_includes: List[str] = field(default_factory=lambda: [])
    as_property: bool = False
    copy_parent_items: bool = False
    proxy: bool = False
    noconstructor: bool = False
    load_priority: int = 0
    rename: str = None
    rename_parameters: List[Tuple[str, str]] = field(default_factory=lambda: [])
    bind_code: str = None
    meta: Set[str] = field(default_factory=lambda: set())
    merge_template_specialisations_as: Optional[str] = None

    def combine(self, flags: "ObidogFlagsModel"):
        self.helpers += flags.helpers
        self.template_hints = {**flags.template_hints, **self.template_hints}
        self.nobind = self.nobind or flags.nobind
        self.additional_includes += flags.additional_includes
        self.as_property = self.as_property or flags.as_property
        self.copy_parent_items = self.copy_parent_items or flags.copy_parent_items
        self.proxy = self.proxy or flags.proxy
        self.noconstructor = self.noconstructor or flags.noconstructor
        self.load_priority = self.load_priority or flags.load_priority
        self.rename = self.rename or flags.rename
        self.rename_parameters = self.rename_parameters or flags.rename_parameters
        self.bind_code = self.bind_code or flags.bind_code
        self.meta = self.meta | flags.meta
        self.merge_template_specialisations_as = (
            self.merge_template_specialisations_as
            or flags.merge_template_specialisations_as
        )
