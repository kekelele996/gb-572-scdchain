from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.controllers import dim_controller

router = APIRouter(prefix="/dims", tags=["dimension-browser"])


@router.get("/current")
def current(
    search: str = "",
    level: str = "",
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
) -> dict:
    return dim_controller.current(db, search, level, page, page_size)


@router.get("/as-of/export")
def export_as_of(as_of: str, db: Session = Depends(get_db)) -> Response:
    return dim_controller.export_as_of(db, as_of)


@router.get("/as-of")
def as_of(
    as_of: str,
    search: str = "",
    level: str = "",
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
) -> dict:
    return dim_controller.as_of(db, as_of, search, level, page, page_size)


@router.get("/attributes")
def attributes() -> dict:
    return dim_controller.attributes()


@router.get("/{business_key}/history")
def history(business_key: str, db: Session = Depends(get_db)) -> dict:
    return dim_controller.history(db, business_key)
