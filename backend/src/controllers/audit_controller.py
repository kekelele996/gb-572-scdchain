from sqlalchemy.orm import Session

from src.services import audit_service, build_service, conflict_service, dimension_service, dim_service


def list_logs(db: Session, limit: int = 100) -> dict:
    return {"items": audit_service.list_logs(db, limit)}


def overview(db: Session) -> dict:
    payload = dim_service.overview(db)
    payload["conflict_summary"] = conflict_service.summary(db)
    payload["sources"] = dimension_service.list_sources(db)
    payload["runs"] = build_service.list_runs(db, 10)
    return payload
