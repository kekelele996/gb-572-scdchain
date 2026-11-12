from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.constants.roles import Role
from src.controllers import build_controller
from src.middlewares.rbac import require_roles
from src.schemas.build import BuildCreateRequest

router = APIRouter(prefix="/builds", tags=["build"])


@router.get("")
def list_runs(limit: int = 20, db: Session = Depends(get_db)) -> dict:
    return build_controller.list_runs(db, limit)


@router.get("/compare")
def compare(left_id: int, right_id: int, db: Session = Depends(get_db)) -> dict:
    return build_controller.compare_runs(db, left_id, right_id)


@router.get("/{run_id}")
def get_run(run_id: int, db: Session = Depends(get_db)) -> dict:
    return build_controller.get_run(db, run_id)


@router.post("", status_code=202)
def create_run(
    payload: BuildCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    actor: dict = Depends(require_roles(Role.ADMIN, Role.MODELER)),
) -> dict:
    return build_controller.create_run(db, payload, actor, request)
