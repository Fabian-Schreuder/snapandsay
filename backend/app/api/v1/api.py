from fastapi import APIRouter

from app.api.v1.endpoints import health, analysis, stream, logs, admin

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(stream.router, prefix="/analysis", tags=["streaming"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

