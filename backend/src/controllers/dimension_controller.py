from sqlalchemy.orm import Session

from src.models.user import User
from src.schemas.dimension import RuleUpdateRequest
from src.services import audit_service, dimension_service, snapshot_service


def list_rules(db: Session) -> dict:
    return {"items": dimension_service.list_rules(db), "sources": dimension_service.list_sources(db)}


def update_rule(db: Session, rule_id: int, payload: RuleUpdateRequest, actor: dict, request) -> dict:
    updated = dimension_service.update_rule(db, rule_id, payload.model_dump(exclude_unset=True), actor["email"])
    audit_service.record(
        db,
        actor_email=actor["email"],
        actor_role=actor["role"],
        action="dimension.rule.update",
        resource_type="merge_rule",
        resource_id=str(rule_id),
        detail={"after": updated},
        ip=request.client.host if request.client else "",
        request_id=getattr(request.state, "request_id", ""),
    )
    return updated


def snapshot_feed(db: Session, limit: int = 20) -> dict:
    return {"summary": snapshot_service.feed_summary(db), "rows": snapshot_service.recent_rows(db, limit)}
