from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination

from app.api.v1.api import api_router
from app.config import settings

from .database import create_db_and_tables
from .utils import simple_generate_unique_route_id


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_db_and_tables()
    yield
    # Shutdown

app = FastAPI(
    title=settings.PROJECT_NAME,
    generate_unique_id_function=simple_generate_unique_route_id,
    openapi_url=settings.OPENAPI_URL,
    lifespan=lifespan,
)


# Middleware for CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

add_pagination(app)


@app.get("/health", tags=["health"])
async def root_health_check():
    """Root-level health check for load balancers and container orchestration."""
    return {"status": "ok"}
