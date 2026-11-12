from pydantic import BaseModel


class SnapshotRowOut(BaseModel):
    id: int
    source_code: str
    source_name: str
    business_key: str
    snapshot_date: str
    attributes: dict
    ingested_at: str
    is_late: bool
    batch_tag: str
