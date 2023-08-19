from enum import Enum

from pydantic import BaseModel, Field

from obidog.models.base import BaseModel


class MetaTag(Enum):
    NonCopyable = "NonCopyable"


class ObidogHookTrigger(Enum):
    Inherit = "Inherit"
    Bind = "Bind"


# note: used to be unsafe_hash
class ObidogHook(BaseModel):
    trigger: ObidogHookTrigger
    code: str

    def __hash__(self) -> int:
        return hash((self.trigger, self.code))


class ObidogFlagsModel(BaseModel):
    helpers: list[str] = Field(default_factory=list)
    template_hints: dict[str, list[str]] = Field(default_factory=dict)
    nobind: bool = False
    additional_includes: list[str] = Field(default_factory=list)
    as_property: bool = False
    copy_parent_items: bool = False
    proxy: bool = False
    noconstructor: bool = False
    load_priority: int = 0
    rename: str = None
    rename_parameters: list[tuple[str, str]] = Field(default_factory=list)
    bind_code: str = None
    meta: set[str] = Field(default_factory=set)
    merge_template_specialisations_as: str | None = None
    hooks: set[ObidogHook] = Field(default_factory=set)

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
        self.hooks = self.hooks | flags.hooks
