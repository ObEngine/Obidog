from dataclasses import dataclass, field
from typing import List

from obidog.models.base import BaseModel


@dataclass
class ObidogFlagsModel(BaseModel):
    bind_to: str = ""
    helpers: List[str] = field(default_factory=lambda: [])
    template_hints: List[str] = field(default_factory=lambda: [])
    abstract: bool = False
    nobind: bool = False
    additional_includes: List[str] = field(default_factory=lambda: [])
    as_property: bool = False
    copy_parent_items: bool = False
    proxy: bool = False
