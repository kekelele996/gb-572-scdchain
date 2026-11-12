"""Celery task: run one SCD2 build batch in the worker container."""
from src.config.celery_app import celery_app
from src.config.database import SessionLocal
from src.services import build_service


@celery_app.task(name="scdchain.run_build", bind=True, max_retries=0)
def run_build(self, run_id: int) -> dict:
    db = SessionLocal()
    try:
        return build_service.execute_run(db, run_id)
    finally:
        db.close()
