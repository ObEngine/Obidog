from typing import List

from obidog.models.base import BaseModel


class ObidogFlagsModel(BaseModel):
    def __init__(
        self,
        bind_to: str = "",
        helpers: List[str] = [],
        template_hints: List[str] = [],
        abstract: bool = False,
        nobind: bool = False,
        additional_includes: List[str] = [],
        as_property: bool = False,
        copy_parent_items: bool = False,
        proxy: bool = False,
    ):
        self.bind_to = bind_to
        self.helpers = helpers
        self.template_hints = template_hints
        self.abstract = abstract
        self.nobind = nobind
        self.additional_includes = additional_includes
        self.as_property = as_property
        self.copy_parent_items = copy_parent_items
        self.proxy = proxy
