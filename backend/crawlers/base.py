"""Base crawler utilities shared by all platform crawlers."""
import asyncio
import hashlib
import html
import logging
import random
import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RawText

logger = logging.getLogger(__name__)

BOT_UA = "JushuBot/1.0 (contact: alexisobrenovic@gmail.com)"

DEFAULT_HEADERS = {
    "User-Agent": BOT_UA,
    "Accept": "application/json",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

_RE_HTML_TAG = re.compile(r"<[^>]+>")
_RE_URL = re.compile(r"https?://\S+", re.IGNORECASE)
_RE_MENTION = re.compile(r"@\S+")
_RE_EMOJI = re.compile(
    "["
    "\U0001F300-\U0001FAFF"  # all major emoji blocks in supplementary planes
    "\U00010000-\U0010FFFF"  # remaining supplementary planes
    "☀-➿"          # misc symbols, dingbats (U+2600–U+27BF, before CJK at U+4E00)
    "⌀-⏿"          # misc technical (⌚ ⏏ etc.)
    "⬀-⯿"          # misc symbols and arrows
    "←-⇿"          # arrows block
    "▪-◾"          # geometric shapes subset used as emoji
    "️"                 # variation selector-16
    "‍"                 # zero-width joiner
    "〰"                 # wavy dash
    "]+",
    flags=re.UNICODE,
)
_RE_WHITESPACE = re.compile(r"[ \t]{2,}")


def clean_text(text: str) -> str:
    """Strip HTML tags, URLs, @mentions, emoji, and excess whitespace."""
    text = _RE_HTML_TAG.sub("", text)
    text = html.unescape(text)
    text = _RE_URL.sub("", text)
    text = _RE_MENTION.sub("", text)
    text = _RE_EMOJI.sub("", text)
    text = _RE_WHITESPACE.sub(" ", text)
    return text.strip()


def sha256_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


async def polite_delay(min_s: float = 1.0, max_s: float = 2.0) -> None:
    delay = random.uniform(min_s, max_s)
    logger.debug("Polite delay: %.2fs", delay)
    await asyncio.sleep(delay)


class BaseCrawler(ABC):
    """Abstract base class for all platform crawlers."""

    def __init__(self, session_factory: Any, max_pages: int = 5) -> None:
        self.session_factory = session_factory
        self.max_pages = max_pages
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "BaseCrawler":
        self.client = httpx.AsyncClient(
            headers=DEFAULT_HEADERS,
            timeout=httpx.Timeout(30.0, connect=5.0),
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
    ) -> bool:
        """
        Insert a raw text record using a short-lived session (no long-held connection).
        Returns True if inserted, False if duplicate or empty after cleaning.
        """
        raw_content = clean_text(raw_content)
        if len(raw_content) < 2:
            return False
        content_hash = sha256_hash(raw_content)

        async with self.session_factory() as db:
            existing = await db.execute(
                select(RawText.id).where(RawText.content_hash == content_hash)
            )
            if existing.scalar_one_or_none() is not None:
                return False

            raw = RawText(
                platform=platform,
                content_type=content_type,
                raw_content=raw_content,
                content_hash=content_hash,
                source_url=source_url,
                timestamp=timestamp or datetime.now(timezone.utc),
                processed=False,
            )
            db.add(raw)
            await db.commit()
            return True

    @abstractmethod
    async def crawl(self) -> None: ...
