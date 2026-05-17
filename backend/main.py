import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.api import search, patterns, tags, admin
from app.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage the async DB connection pool lifecycle."""
    logger.info("Starting up — initialising database connection pool.")
    # Engine is created at import time; we do a quick connectivity check here.
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("Database connection pool ready.")
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("Shutting down — disposing database connection pool.")
    await engine.dispose()
    logger.info("Database connection pool disposed.")


app = FastAPI(
    title="JuShi API",
    description="API for indexing and searching Chinese intertextual sentence frames",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(patterns.router, prefix="/api", tags=["patterns"])
app.include_router(tags.router, prefix="/api", tags=["tags"])
app.include_router(admin.router, prefix="/api", tags=["admin"])


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """
    Lightweight liveness + DB connectivity probe.
    Returns 200 if the database is reachable, 503 otherwise.
    """
    from fastapi.responses import JSONResponse

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        logger.error("Health check failed: %s", exc)
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "unreachable", "detail": str(exc)},
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
