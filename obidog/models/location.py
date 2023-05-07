from obidog.models.base import BaseModel


class Location(BaseModel):
    file: str = ""
    line: int = -1
    column: int = -1


# Only use as a parameter annotation
# location is optional and this should not be used as base class
class LocalizableModel(BaseModel):
    location: Location
