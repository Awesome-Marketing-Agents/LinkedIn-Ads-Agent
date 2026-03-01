"""FastAPI application: CORS, exception handlers, request context middleware, lifespan."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.errors.exceptions import LinkedInActionCenterError
from app.routes import api_router
from app.utils.logging import (
    generate_request_id,
    get_logger,
    request_id_var,
    setup_logging,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.LOG_LEVEL)
    logger.info("Starting LinkedIn Ads Action Center")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="LinkedIn Ads Action Center",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request context middleware — sets request_id and logs request completion
@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    rid = request.headers.get("X-Request-ID") or generate_request_id()
    token = request_id_var.set(rid)
    start = time.monotonic()

    try:
        response = await call_next(request)
        duration = time.monotonic() - start
        logger.info(
            "%s %s -> %d (%.2fs)",
            request.method, request.url.path, response.status_code, duration,
        )
        response.headers["X-Request-ID"] = rid
        return response
    finally:
        request_id_var.reset(token)


# Exception handlers
@app.exception_handler(LinkedInActionCenterError)
async def app_error_handler(request: Request, exc: LinkedInActionCenterError):
    status_code = 500
    if hasattr(exc, "status_code") and exc.status_code:
        status_code = exc.status_code
    elif "Authentication" in type(exc).__name__:
        status_code = 401

    return JSONResponse(
        status_code=status_code,
        content={"error": exc.message, "details": exc.details},
    )


# Mount all routes
app.include_router(api_router)
