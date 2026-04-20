from typing import Literal

from pydantic import BaseModel, Field


LocationSearchKind = Literal["origin", "destination"]


class LocationSearchSuggestion(BaseModel):
    id: str = Field(..., min_length=1, max_length=200)
    label: str = Field(..., min_length=1, max_length=160)
    detail: str | None = Field(default=None, max_length=240)


class LocationSearchResponse(BaseModel):
    items: list[LocationSearchSuggestion] = Field(default_factory=list)
