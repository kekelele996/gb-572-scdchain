from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.constants.roles import Role
from src.controllers import dimension_controller
from src.middlewares.rbac import require_roles
from src.schemas.dimension import RuleUpdateRequest

router = APIRouter(prefix="/dimensions", tags=["dimension"])


@router.get("/rules")
def list_rules(db: Session = Depends(get_db)) -> dict:
    return dimension_controller.list_rules(db)


@router.put("/rules/{rule_id}")
def update_rule(
    rule_id: int,
    payload: RuleUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    actor: dict = Depends(require_roles(Role.ADMIN)),
) -> dict:
    return dimension_controller.update_rule(db, rule_id, payload, actor, request)
