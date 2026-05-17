import asyncio
import logging
from typing import Any, Dict, List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings

logger = logging.getLogger(__name__)

_scheduler: Optional[AsyncIOScheduler] = None
_crawl_lock: Optional[asyncio.Lock] = None
_pipeline_lock: Optional[asyncio.Lock] = None


def _get_crawl_lock() -> asyncio.Lock:
    global _crawl_lock
    if _crawl_lock is None:
        _crawl_lock = asyncio.Lock()
    return _crawl_lock


def _get_pipeline_lock() -> asyncio.Lock:
    global _pipeline_lock
    if _pipeline_lock is None:
        _pipeline_lock = asyncio.Lock()
    return _pipeline_lock


async def run_scheduled_bilibili_crawl() -> Dict[str, Any]:
    from app.database import AsyncSessionLocal
    from crawlers.bilibili import BilibiliCrawler

    crawl_lock = _get_crawl_lock()
    if crawl_lock.locked():
        logger.warning("Skipping scheduled Bilibili crawl because a crawl is already running.")
        return {"status": "skipped", "reason": "crawl_already_running"}

    async with crawl_lock:
        crawler = BilibiliCrawler(
            session_factory=AsyncSessionLocal,
            max_pages=settings.BILIBILI_SCHEDULED_MAX_PAGES,
            max_danmaku=settings.BILIBILI_SCHEDULED_MAX_DANMAKU,
        )
        keywords = [kw.strip() for kw in settings.BILIBILI_SCHEDULED_KEYWORDS if kw.strip()]
        bvids: List[str] = []
        seen: set[str] = set()

        async with crawler:
            for keyword in keywords:
                keyword_bvids = await crawler._search_bvids(
                    keyword,
                    settings.BILIBILI_SCHEDULED_KEYWORD_RESULTS,
                )
                for bvid in keyword_bvids:
                    if bvid in seen:
                        continue
                    seen.add(bvid)
                    bvids.append(bvid)

        if not bvids:
            logger.info("Scheduled Bilibili crawl found no videos for keywords=%s", keywords)
            return {"status": "ok", "keywords": keywords, "bvid_count": 0, "saved_total": 0}

        totals = await crawler.crawl_bvids(bvids)
        saved_total = sum(totals.values())
        logger.info(
            "Scheduled Bilibili crawl completed: %d video(s), %d new raw text(s).",
            len(bvids),
            saved_total,
        )
        return {
            "status": "ok",
            "keywords": keywords,
            "bvid_count": len(bvids),
            "saved_total": saved_total,
            "totals": totals,
        }


async def run_scheduled_pipeline() -> Dict[str, Any]:
    from nlp.run_pipeline import run_pipeline

    pipeline_lock = _get_pipeline_lock()
    if pipeline_lock.locked():
        logger.warning("Skipping scheduled NLP pipeline because a pipeline run is already active.")
        return {"status": "skipped", "reason": "pipeline_already_running"}

    async with pipeline_lock:
        await run_pipeline()
        logger.info("Scheduled NLP pipeline run completed.")
        return {"status": "ok"}


def _job_wrapper(coro_func):
    async def _runner() -> None:
        try:
            await coro_func()
        except Exception:
            logger.exception("Scheduled job %s failed.", coro_func.__name__)

    return _runner


def _build_cron_trigger(expr: str) -> CronTrigger:
    return CronTrigger.from_crontab(expr, timezone=settings.SCRAPER_SCHEDULE_TIMEZONE)


def start_scheduler() -> Optional[AsyncIOScheduler]:
    global _scheduler

    if not settings.SCRAPER_SCHEDULER_ENABLED:
        logger.info("Scraper scheduler disabled by configuration.")
        return None

    if _scheduler is not None and _scheduler.running:
        return _scheduler

    scheduler = AsyncIOScheduler(timezone=settings.SCRAPER_SCHEDULE_TIMEZONE)

    scheduler.add_job(
        _job_wrapper(run_scheduled_bilibili_crawl),
        trigger=_build_cron_trigger(settings.BILIBILI_CRAWL_CRON),
        id="scheduled_bilibili_crawl",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        _job_wrapper(run_scheduled_pipeline),
        trigger=_build_cron_trigger(settings.NLP_PIPELINE_CRON),
        id="scheduled_nlp_pipeline",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    scheduler.start()
    _scheduler = scheduler
    logger.info(
        "Scraper scheduler started with jobs: bilibili=%r pipeline=%r timezone=%s",
        settings.BILIBILI_CRAWL_CRON,
        settings.NLP_PIPELINE_CRON,
        settings.SCRAPER_SCHEDULE_TIMEZONE,
    )
    return scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is None:
        return
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
    _scheduler = None
    logger.info("Scraper scheduler stopped.")


def get_scheduler_status() -> Dict[str, Any]:
    jobs: List[Dict[str, Any]] = []
    if _scheduler is not None:
        for job in _scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger),
                }
            )

    return {
        "enabled": settings.SCRAPER_SCHEDULER_ENABLED,
        "running": bool(_scheduler and _scheduler.running),
        "timezone": settings.SCRAPER_SCHEDULE_TIMEZONE,
        "jobs": jobs,
        "bilibili_keywords": settings.BILIBILI_SCHEDULED_KEYWORDS,
    }
