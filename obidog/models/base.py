from dataclasses import dataclass
from enum import Enum


@dataclass
class BaseModel:
    pass


class ItemVisibility(Enum):
    Private = "private"
    Protected = "protected"
    Public = "public"


# Only use as a parameter annotation
# location is optional and this should not be used as base class
@dataclass
class LocalizableModel(BaseModel):
    location: "Location"
