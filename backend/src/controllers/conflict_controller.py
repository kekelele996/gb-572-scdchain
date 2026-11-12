from fastapi import Request
from sqlalchemy.orm import Session

from src.schemas.conflict import ConflictResolveRequest
from src.services import audit_service, conflict_service
from src.utils.pagination import pagination


def list_conflicts(db: Session, status: str = "all", page: int = 1, page_size: int = 20) -> dict:
    return conflict_service.list_conflicts(db, status, pagination(page, page_size))


def summary(db: Session) -> dict:
    return conflict_service.summary(db)


def resolve(db: Session, conflict_id: int, payload: ConflictResolveRequest, actor: dict, request: Request) -> dict:
    result = conflict_service.resolve(
        db,
        conflict_id,
        strategy=payload.strategy,
        value=payload.value,
        note=payload.note,
        actor_email=actor["email"],
    )
    audit_service.record(
        db,
        actor_email=actor["email"],
        actor_role=actor["role"],
        action="conflict.resolve",
        resource_type="conflict_item",
        resource_id=str(conflict_id),
        detail={"strategy": payload.strategy, "value": payload.value, "note": payload.note},
        ip=request.client.host if request.client else "",
        request_id=getattr(request.state, "request_id", ""),
    )
    return result
