import asyncio
import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import RawText, SentencePattern, PatternExample

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request / Response Schemas ────────────────────────────────────────────────

class CrawlRequest(BaseModel):
    bvids: list[str] = []
    max_pages: int = 5


class CrawlResponse(BaseModel):
    status: str
    message: str
    task_id: Optional[str] = None


class StatsResponse(BaseModel):
    raw_texts: int
    patterns: int
    examples: int
    unprocessed_texts: int


# ── Background task ───────────────────────────────────────────────────────────

async def _run_bilibili_crawl(bvids: list[str], max_pages: int) -> None:
    """Run crawl in background; import lazily to avoid circular imports."""
    try:
        from crawlers.bilibili import BilibiliCrawler
        from app.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            crawler = BilibiliCrawler(db=db, max_pages=max_pages)
            await crawler.crawl_bvids(bvids)
            await db.commit()
        logger.info("Bilibili crawl completed for bvids: %s", bvids)
    except Exception as exc:
        logger.exception("Bilibili crawl failed: %s", exc)


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/admin/crawl/trigger", response_model=CrawlResponse)
async def trigger_crawl(
    payload: CrawlRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> CrawlResponse:
    """
    Enqueue a Bilibili crawl job as a FastAPI background task.
    Returns immediately; crawl runs asynchronously.
    """
    if not payload.bvids:
        raise HTTPException(status_code=422, detail="At least one BV number is required.")

    background_tasks.add_task(_run_bilibili_crawl, payload.bvids, payload.max_pages)

    return CrawlResponse(
        status="accepted",
        message=f"Crawl triggered for {len(payload.bvids)} BV number(s). Running in background.",
    )


@router.get("/admin/stats", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)) -> StatsResponse:
    """Return aggregate counts for monitoring."""
    raw_count = (await db.execute(select(func.count()).select_from(RawText))).scalar_one()
    unprocessed_count = (
        await db.execute(
            select(func.count()).select_from(RawText).where(RawText.processed == False)  # noqa: E712
        )
    ).scalar_one()
    pattern_count = (
        await db.execute(select(func.count()).select_from(SentencePattern))
    ).scalar_one()
    example_count = (
        await db.execute(select(func.count()).select_from(PatternExample))
    ).scalar_one()

    return StatsResponse(
        raw_texts=raw_count,
        patterns=pattern_count,
        examples=example_count,
        unprocessed_texts=unprocessed_count,
    )
