from typing import Literal

from pydantic import BaseModel, Field


class ConflictResolveRequest(BaseModel):
    strategy: Literal["candidate", "manual"]
    value: str = Field(min_length=1, max_length=64)
    note: str = Field(default="", max_length=200)
