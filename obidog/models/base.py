from dataclasses import dataclass
from enum import Enum


@dataclass
class BaseModel:
    pass


class ItemVisibility(Enum):
    Private = "private"
    Protected = "protected"
    Public = "public"
