from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.constants.roles import Role
from src.controllers import conflict_controller
from src.middlewares.rbac import require_roles
from src.schemas.conflict import ConflictResolveRequest

router = APIRouter(prefix="/conflicts", tags=["conflict"])


@router.get("")
def list_conflicts(status: str = "all", page: int = 1, page_size: int = 20, db: Session = Depends(get_db)) -> dict:
    return conflict_controller.list_conflicts(db, status, page, page_size)


@router.get("/summary")
def summary(db: Session = Depends(get_db)) -> dict:
    return conflict_controller.summary(db)


@router.post("/{conflict_id}/resolve")
def resolve(
    conflict_id: int,
    payload: ConflictResolveRequest,
    request: Request,
    db: Session = Depends(get_db),
    actor: dict = Depends(require_roles(Role.ADMIN, Role.MODELER)),
) -> dict:
    return conflict_controller.resolve(db, conflict_id, payload, actor, request)
