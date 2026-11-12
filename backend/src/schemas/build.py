from pydantic import BaseModel, Field


class BuildCreateRequest(BaseModel):
    notes: str = Field(default="", max_length=200)
    label: str | None = Field(default=None, max_length=60)
