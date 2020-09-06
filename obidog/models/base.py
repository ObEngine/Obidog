from dataclasses import dataclass


@dataclass
class BaseModel:
    pass


# Only use as a parameter annotation
# location is optional and this should not be used as base class
@dataclass
class LocalizableModel(BaseModel):
    location: "Location"
