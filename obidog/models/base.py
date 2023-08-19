from enum import Enum

from pydantic import BaseModel


class CppElement(BaseModel):
    id: str = ""


class ItemVisibility(Enum):
    Private = "private"
    Protected = "protected"
    Public = "public"
