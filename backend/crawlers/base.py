"""Base crawler utilities shared by all platform crawlers."""
import asyncio
import hashlib
import logging
import random
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RawText

logger = logging.getLogger(__name__)

BOT_UA = "JushuBot/1.0 (contact: alexisobrenovic@gmail.com)"

DEFAULT_HEADERS = {
    "User-Agent": BOT_UA,
    "Accept": "application/json",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


def sha256_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


async def polite_delay(min_s: float = 1.0, max_s: float = 2.0) -> None:
    """Sleep for a random interval to be polite to remote servers."""
    delay = random.uniform(min_s, max_s)
    logger.debug("Polite delay: %.2fs", delay)
    await asyncio.sleep(delay)


class BaseCrawler(ABC):
    """Abstract base class for all platform crawlers."""

    def __init__(self, db: AsyncSession, max_pages: int = 5) -> None:
        self.db = db
        self.max_pages = max_pages
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "BaseCrawler":
        self.client = httpx.AsyncClient(
            headers=DEFAULT_HEADERS,
            timeout=httpx.Timeout(15.0, connect=5.0),
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self.client:
            await self.client.aclose()

    async def _get_json(self, url: str, params: Optional[Dict[str, Any]] = None) -> Any:
        assert self.client is not None, "Client not initialised — use async context manager."
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def save_raw_text(
        self,
        *,
        platform: str,
        content_type: str,
        raw_content: str,
        source_url: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> Optional[RawText]:
        """
        Insert a raw text record into the DB with deduplication via SHA-256.
        Returns the new record, or None if it already existed.
        """
        from sqlalchemy import select

        content_hash = sha256_hash(raw_content)

        # Deduplication check
        existing = await self.db.execute(
            select(RawText.id).where(RawText.content_hash == content_hash)
        )
        if existing.scalar_one_or_none() is not None:
            logger.debug("Skipping duplicate content (hash=%s)", content_hash[:12])
            return None

        raw = RawText(
            platform=platform,
            content_type=content_type,
            raw_content=raw_content,
            content_hash=content_hash,
            source_url=source_url,
            timestamp=timestamp or datetime.now(timezone.utc),
            processed=False,
        )
        self.db.add(raw)
        await self.db.flush()  # get the auto-generated id without full commit
        return raw

    @abstractmethod
    async def crawl(self) -> None:
        """Subclasses implement the main crawl logic here."""
        ...
