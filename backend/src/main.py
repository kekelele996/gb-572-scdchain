"""scdchain API entrypoint.

Middleware order (outermost first):
    CORS -> RequestId -> Auth -> RateLimit -> Audit -> routes -> error handlers
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.database import init_db
from src.config.settings import settings
from src.middlewares.audit_logger import AuditMiddleware
from src.middlewares.auth import AuthMiddleware
from src.middlewares.error_handler import RequestIdMiddleware, install_error_handlers
from src.middlewares.rate_limit import RateLimitMiddleware
from src.routes import audit, auth, build, conflict, dim, dimension, health, meta, snapshot
from src.utils.logger import log_event


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if settings.SEED_DEMO:
        try:
            from scripts.seed_demo import run_seed

            result = run_seed()
            log_event("SEED_DEMO_FINISHED", **result)
        except Exception as exc:  # seed must never block startup
            log_event("SEED_DEMO_FAILED", error=f"{type(exc).__name__}: {exc}")
    yield


app = FastAPI(
    title="SCD Chain API",
    description="缓慢变化维 SCD2 拉链构建与跨源一致性维度台 — 嘉禾保险数据仓库建模组",
    version="1.0.0",
    lifespan=lifespan,
)

install_error_handlers(app)

# added first => innermost
app.add_middleware(AuditMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(RequestIdMiddleware)
# added last => outermost (CORS preflight is answered before auth)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "Content-Disposition"],
)

# Compose routes `/api/` through Nginx to `backend:8000/` (prefix stripped);
# mounting the same routers under both prefixes keeps curl and the SPA identical.
for _prefix in ("", "/api"):
    app.include_router(health.router, prefix=_prefix)
    app.include_router(auth.router, prefix=_prefix)
    app.include_router(dimension.router, prefix=_prefix)
    app.include_router(snapshot.router, prefix=_prefix)
    app.include_router(build.router, prefix=_prefix)
    app.include_router(dim.router, prefix=_prefix)
    app.include_router(conflict.router, prefix=_prefix)
    app.include_router(audit.router, prefix=_prefix)
    app.include_router(meta.router, prefix=_prefix)


@app.get("/")
def index() -> dict:
    return {
        "service": "scdchain-backend",
        "brand": "scdchain",
        "docs": "/docs",
        "endpoints": [
            "/health",
            "/auth/login",
            "/meta/overview",
            "/dimensions/rules",
            "/snapshots/feed",
            "/builds",
            "/builds/{id}",
            "/builds/compare",
            "/dims/current",
            "/dims/as-of",
            "/dims/as-of/export",
            "/conflicts",
            "/conflicts/{id}/resolve",
        ],
    }
