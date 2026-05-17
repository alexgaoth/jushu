import logging
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import RawText, SentencePattern, PatternExample
from app.scheduler import get_scheduler_status, run_scheduled_bilibili_crawl, run_scheduled_pipeline

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


class SchedulerStatusResponse(BaseModel):
    enabled: bool
    running: bool
    timezone: str
    jobs: list[dict]
    bilibili_keywords: list[str]


# ── Background task ───────────────────────────────────────────────────────────

async def _run_bilibili_crawl(bvids: list[str], max_pages: int) -> None:
    """Run crawl in background; import lazily to avoid circular imports."""
    try:
        from crawlers.bilibili import BilibiliCrawler
        from app.database import AsyncSessionLocal

        crawler = BilibiliCrawler(session_factory=AsyncSessionLocal, max_pages=max_pages)
        await crawler.crawl_bvids(bvids)
        logger.info("Bilibili crawl completed for bvids: %s", bvids)
    except Exception as exc:
        logger.exception("Bilibili crawl failed: %s", exc)


async def _run_scheduled_crawl_now() -> None:
    try:
        await run_scheduled_bilibili_crawl()
    except Exception as exc:
        logger.exception("Scheduled crawl-now run failed: %s", exc)


async def _run_scheduled_pipeline_now() -> None:
    try:
        await run_scheduled_pipeline()
    except Exception as exc:
        logger.exception("Scheduled pipeline-now run failed: %s", exc)


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/admin/crawl/trigger", response_model=CrawlResponse)
async def trigger_crawl(
    payload: CrawlRequest,
    background_tasks: BackgroundTasks,
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


@router.get("/admin/scheduler", response_model=SchedulerStatusResponse)
async def scheduler_status() -> SchedulerStatusResponse:
    return SchedulerStatusResponse(**get_scheduler_status())


@router.post("/admin/scheduler/crawl-now", response_model=CrawlResponse)
async def run_scheduler_crawl_now(background_tasks: BackgroundTasks) -> CrawlResponse:
    background_tasks.add_task(_run_scheduled_crawl_now)
    return CrawlResponse(
        status="accepted",
        message="Scheduled keyword crawl triggered in background.",
    )


@router.post("/admin/scheduler/pipeline-now", response_model=CrawlResponse)
async def run_scheduler_pipeline_now(background_tasks: BackgroundTasks) -> CrawlResponse:
    background_tasks.add_task(_run_scheduled_pipeline_now)
    return CrawlResponse(
        status="accepted",
        message="Scheduled NLP pipeline triggered in background.",
    )
