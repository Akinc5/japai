from dotenv import load_dotenv

load_dotenv()

import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from apps.api.core.llm_client import LLMResponseError, LLMUnavailableError

logger = logging.getLogger("ja_assure.api")

from apps.api.routers import (
    brands,
    campaigns,
    content,
    demo,
    events,
    health,
    leads,
    metrics,
    observability,
    opportunities,
    optimization,
    research,
    repurpose,
    review,
    visual,
)

import re
import time
from collections import defaultdict

app = FastAPI(title="JAPAI - AI Marketing OS", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_IP_REQUESTS = defaultdict(list)
_GENERATIVE_PATHS = {"/content/generate", "/demo/run", "/repurpose/generate", "/visual/generate", "/optimization/analyze"}
_MAX_GENERATIVE_PER_MINUTE = 15
_MAX_GENERAL_PER_MINUTE = 60


@app.middleware("http")
async def rate_limit_and_path_middleware(request: Request, call_next):
    # 1. Normalize multiple slashes in path
    path = request.scope.get("path", "")
    if "//" in path:
        path = re.sub(r"/+", "/", path)
        request.scope["path"] = path

    # 2. Rate limit protection for non-stop spamming
    client_ip = request.client.host if request.client else "127.0.0.1"
    now = time.time()
    
    # Filter timestamps older than 60s
    recent_all = [t for t in _IP_REQUESTS[client_ip] if now - t < 60]
    _IP_REQUESTS[client_ip] = recent_all

    is_gen = any(p in path for p in _GENERATIVE_PATHS)
    limit = _MAX_GENERATIVE_PER_MINUTE if is_gen else _MAX_GENERAL_PER_MINUTE

    if len(recent_all) >= limit:
        retry_after = int(60 - (now - recent_all[0])) + 1
        return JSONResponse(
            status_code=429,
            content={
                "error": "rate_limited",
                "detail": f"Rate limit reached ({limit} reqs/min). Please wait {retry_after}s.",
                "retry_after_seconds": max(retry_after, 1),
            },
            headers={"Retry-After": str(max(retry_after, 1))},
        )

    _IP_REQUESTS[client_ip].append(now)
    return await call_next(request)




@app.on_event("startup")
def on_startup():
    try:
        from apps.api.models.base import Base
        from apps.api.core.db import engine, SessionLocal
        import apps.api.models

        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created successfully.")

        db = SessionLocal()
        try:
            from apps.api.models import Brand

            if db.query(Brand).count() == 0:
                logger.info("Seeding initial brands and knowledge chunks...")
                from db.seed.seed_brands import run as seed_brands

                seed_brands()
        finally:
            db.close()
    except Exception as e:
        logger.error("Startup database initialization error: %s", e)


app.include_router(health.router, tags=["health"])
app.include_router(content.router)
app.include_router(review.router)
app.include_router(metrics.router)
app.include_router(brands.router)
app.include_router(research.router)
app.include_router(opportunities.router)
app.include_router(campaigns.router)
app.include_router(leads.router)
app.include_router(optimization.router)
app.include_router(observability.router)
app.include_router(events.router)
app.include_router(visual.router)
app.include_router(repurpose.router)
app.include_router(demo.router)


@app.exception_handler(LLMUnavailableError)
def handle_llm_unavailable(request: Request, exc: LLMUnavailableError):
    logger.warning("LLM unavailable on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=503,
        content={
            "error": "llm_unavailable",
            "detail": str(exc),
            "hint": "The Gemini API call failed (quota, network, or credentials). "
            "Check GEMINI_API_KEY and daily quota, then retry.",
        },
    )


@app.exception_handler(LLMResponseError)
def handle_llm_response(request: Request, exc: LLMResponseError):
    logger.warning("Malformed LLM response on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=502,
        content={
            "error": "llm_bad_response",
            "detail": str(exc),
            "hint": "The model returned output that did not match the required schema. Retry.",
        },
    )


@app.exception_handler(ValueError)
def handle_value_error(request: Request, exc: ValueError):
    """Agents raise ValueError for not-found/invalid input; never let that 500."""
    logger.info("Bad request on %s: %s", request.url.path, exc)
    return JSONResponse(status_code=400, content={"error": "bad_request", "detail": str(exc)})


@app.exception_handler(Exception)
def handle_unexpected(request: Request, exc: Exception):
    """Last line of defence: a live demo must never render a raw traceback."""
    logger.error("Unhandled error on %s\n%s", request.url.path, traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "detail": f"{type(exc).__name__}: {str(exc)[:200]}",
            "hint": "Full traceback is in the api container logs.",
        },
    )


@app.get("/")
def root():
    return {"service": "ja-assure-ai-marketing-os", "status": "running", "phase": 10}
