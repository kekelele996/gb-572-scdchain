from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.controllers import dimension_controller
from src.schemas.snapshot import SnapshotRowOut

router = APIRouter(prefix="/snapshots", tags=["snapshot"])


@router.get("/feed")
def feed(limit: int = 12, db: Session = Depends(get_db)) -> dict:
    return dimension_controller.snapshot_feed(db, limit)
