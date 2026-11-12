from fastapi import Request
from sqlalchemy.orm import Session

from src.schemas.build import BuildCreateRequest
from src.services import audit_service, build_service


def list_runs(db: Session, limit: int = 20) -> dict:
    return {"items": build_service.list_runs(db, limit)}


def get_run(db: Session, run_id: int) -> dict:
    return build_service.run_detail(db, run_id)


def create_run(db: Session, payload: BuildCreateRequest, actor: dict, request: Request) -> dict:
    run = build_service.create_run(
        db, actor_email=actor["email"], label=payload.label, notes=payload.notes, dispatch=True
    )
    audit_service.record(
        db,
        actor_email=actor["email"],
        actor_role=actor["role"],
        action="build.run.create",
        resource_type="build_run",
        resource_id=str(run.id),
        detail={"run_no": run.run_no, "label": run.label, "notes": payload.notes},
        ip=request.client.host if request.client else "",
        request_id=getattr(request.state, "request_id", ""),
    )
    return build_service.run_payload(run)


def compare_runs(db: Session, left_id: int, right_id: int) -> dict:
    return build_service.compare_runs(db, left_id, right_id)
