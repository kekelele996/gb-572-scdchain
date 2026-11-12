from pydantic import BaseModel, Field


class RuleUpdateRequest(BaseModel):
    source_priority: list[str] | None = None
    normalization: str | None = None
    exclude_from_change: bool | None = None
    description: str | None = Field(default=None, max_length=255)
