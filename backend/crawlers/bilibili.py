"""
Bilibili crawler — fetches comments and danmaku for given BV numbers.

Usage (CLI):
    python -m crawlers.bilibili --bvs BV1xx411c7mD BV2yy222c2mE

The crawler:
  1. Resolves BV -> AID/CID via the Bilibili video info API.
  2. Fetches paginated comments from the reply API.
  3. Fetches danmaku from the danmaku list API.
  4. Stores all texts in raw_texts with SHA-256 deduplication.
  5. Inserts polite 1–2 second random delays between requests.
"""
import argparse
import asyncio
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx

from crawlers.base import BaseCrawler, polite_delay

logger = logging.getLogger(__name__)

# API endpoints
BILIBILI_VIDEO_INFO = "https://api.bilibili.com/x/web-interface/view"
BILIBILI_REPLY_MAIN = "https://api.bilibili.com/x/v2/reply/main"
BILIBILI_DANMAKU = "https://api.bilibili.com/x/v1/dm/list.so"


class BilibiliCrawler(BaseCrawler):
    """Crawl Bilibili comments and danmaku for a list of BV numbers."""

    async def crawl(self) -> None:
        """Not used directly — call crawl_bvids() instead."""
        raise NotImplementedError("Call crawl_bvids(bvids) directly.")

    async def crawl_bvids(self, bvids: List[str]) -> None:
        """Entry point: crawl a list of BV numbers."""
        async with self:
            for bvid in bvids:
                logger.info("Processing %s", bvid)
                try:
                    aid, cid, title = await self._resolve_bvid(bvid)
                    logger.info("  Resolved %s -> aid=%d cid=%d title=%r", bvid, aid, cid, title)
                    video_url = f"https://www.bilibili.com/video/{bvid}"
                    await self._crawl_comments(aid=aid, source_url=video_url)
                    await self._crawl_danmaku(cid=cid, source_url=video_url)
                except httpx.HTTPError as exc:
                    logger.error("HTTP error for %s: %s", bvid, exc)
                except Exception as exc:
                    logger.exception("Unexpected error for %s: %s", bvid, exc)

    # ── Private helpers ─────────────────────────────────────────────────────────

    async def _resolve_bvid(self, bvid: str) -> Tuple[int, int, str]:
        """Return (aid, cid, title) for the given BV number."""
        data = await self._get_json(BILIBILI_VIDEO_INFO, params={"bvid": bvid})
        if data.get("code") != 0:
            raise ValueError(f"Bilibili API error for {bvid}: {data.get('message')}")
        video_data = data["data"]
        aid: int = video_data["aid"]
        # cid is in pages[0] for the default page
        cid: int = video_data["pages"][0]["cid"]
        title: str = video_data.get("title", "")
        await polite_delay()
        return aid, cid, title

    async def _crawl_comments(self, aid: int, source_url: str) -> None:
        """Fetch paginated comments for an AID and store them."""
        for page in range(1, self.max_pages + 1):
            logger.info("  Fetching comments page %d for aid=%d", page, aid)
            try:
                data = await self._get_json(
                    BILIBILI_REPLY_MAIN,
                    params={"type": 1, "oid": aid, "ps": 20, "pn": page, "mode": 3},
                )
            except httpx.HTTPError as exc:
                logger.warning("  Comment fetch failed (page %d): %s", page, exc)
                break

            if data.get("code") != 0:
                logger.warning("  API error on comment page %d: %s", page, data.get("message"))
                break

            replies: List[Dict[str, Any]] = (
                data.get("data", {}).get("replies") or []
            )
            if not replies:
                logger.info("  No more comments on page %d", page)
                break

            saved = 0
            for reply in replies:
                content: str = reply.get("content", {}).get("message", "").strip()
                if not content:
                    continue
                ts_raw = reply.get("ctime")
                ts = (
                    datetime.fromtimestamp(ts_raw, tz=timezone.utc) if ts_raw else None
                )
                result = await self.save_raw_text(
                    platform="bilibili",
                    content_type="comment",
                    raw_content=content,
                    source_url=source_url,
                    timestamp=ts,
                )
                if result:
                    saved += 1

                # Recurse into replies-to-replies (sub-replies)
                sub_replies: List[Dict[str, Any]] = reply.get("replies") or []
                for sub in sub_replies:
                    sub_content: str = sub.get("content", {}).get("message", "").strip()
                    if not sub_content:
                        continue
                    sub_ts_raw = sub.get("ctime")
                    sub_ts = (
                        datetime.fromtimestamp(sub_ts_raw, tz=timezone.utc)
                        if sub_ts_raw
                        else None
                    )
                    await self.save_raw_text(
                        platform="bilibili",
                        content_type="comment",
                        raw_content=sub_content,
                        source_url=source_url,
                        timestamp=sub_ts,
                    )

            logger.info("  Saved %d new comments from page %d", saved, page)
            await polite_delay()

    async def _crawl_danmaku(self, cid: int, source_url: str) -> None:
        """Fetch danmaku XML for a CID and store each danmaku entry."""
        logger.info("  Fetching danmaku for cid=%d", cid)
        assert self.client is not None
        try:
            response = await self.client.get(
                BILIBILI_DANMAKU,
                params={"oid": cid},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("  Danmaku fetch failed for cid=%d: %s", cid, exc)
            return

        # Bilibili returns an XML document like:
        # <i><d p="...">danmaku text</d></i>
        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as exc:
            logger.warning("  Failed to parse danmaku XML: %s", exc)
            return

        saved = 0
        for d_elem in root.findall("d"):
            text_content = (d_elem.text or "").strip()
            if not text_content:
                continue
            # p attribute: "time,type,size,color,timestamp,pool,user_hash,dmid"
            p_attr = d_elem.get("p", "")
            parts = p_attr.split(",")
            ts: Optional[datetime] = None
            if len(parts) >= 5:
                try:
                    ts = datetime.fromtimestamp(int(parts[4]), tz=timezone.utc)
                except (ValueError, OSError):
                    ts = None

            result = await self.save_raw_text(
                platform="bilibili",
                content_type="danmaku",
                raw_content=text_content,
                source_url=source_url,
                timestamp=ts,
            )
            if result:
                saved += 1

        logger.info("  Saved %d new danmaku for cid=%d", saved, cid)
        await polite_delay()


# ── CLI entry point ──────────────────────────────────────────────────────────

async def _main() -> None:
    parser = argparse.ArgumentParser(description="Bilibili crawler for 句式搜索引擎")
    parser.add_argument(
        "--bvs",
        nargs="+",
        required=True,
        metavar="BVID",
        help="One or more BV numbers, e.g. BV1xx411c7mD",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=5,
        help="Maximum number of comment pages to fetch per video (default: 5)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        crawler = BilibiliCrawler(db=db, max_pages=args.max_pages)
        await crawler.crawl_bvids(args.bvs)
        await db.commit()
        logger.info("Crawl complete.")


if __name__ == "__main__":
    asyncio.run(_main())
