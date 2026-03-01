"""APIRouter aggregator — mounts all sub-routers under /api/v1."""

from fastapi import APIRouter

from app.routes.auth import router as auth_router
from app.routes.health import router as health_router
from app.routes.report import router as report_router
from app.routes.status import router as status_router
from app.routes.sync import router as sync_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(sync_router, prefix="/sync", tags=["sync"])
api_router.include_router(report_router, prefix="/report", tags=["report"])
api_router.include_router(status_router, prefix="/status", tags=["status"])
api_router.include_router(health_router, prefix="/health", tags=["health"])
