"""
Bilibili crawler — fetches comments and danmaku for given BV numbers.

Usage (CLI):
    python -m crawlers.bilibili --bvs BV1xx411c7mD BV2yy222c2mE
    python -m crawlers.bilibili --trending 20
    python -m crawlers.bilibili --trending 10 --bvs BV1xx411c7mD

The crawler:
  1. Resolves BV -> AID/CID via the Bilibili video info API.
  2. Fetches paginated comments from the reply API (requires no auth for public videos).
  3. Fetches danmaku XML (capped at --max-danmaku entries per video).
  4. Stores all texts in raw_texts with SHA-256 deduplication via short-lived sessions.
  5. Inserts polite 1-2 second random delays between requests.
  6. Processes up to 3 BVIDs concurrently via asyncio.Semaphore.
"""
import argparse
import asyncio
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx

from crawlers.base import BaseCrawler, polite_delay

logger = logging.getLogger(__name__)

BILIBILI_VIDEO_INFO = "https://api.bilibili.com/x/web-interface/view"
BILIBILI_REPLY_MAIN = "https://api.bilibili.com/x/v2/reply/main"
BILIBILI_DANMAKU = "https://api.bilibili.com/x/v1/dm/list.so"
BILIBILI_POPULAR = "https://api.bilibili.com/x/web-interface/popular"

_CONCURRENCY = 3


class BilibiliCrawler(BaseCrawler):

    def __init__(self, session_factory: Any, max_pages: int = 5, max_danmaku: int = 300) -> None:
        super().__init__(session_factory, max_pages)
        self.max_danmaku = max_danmaku

    async def crawl(self) -> None:
        raise NotImplementedError("Call crawl_bvids(bvids) directly.")

    async def _fetch_trending_bvids(self, n: int) -> List[str]:
        """Page through the Bilibili popular API and return up to n BVIDs."""
        assert self.client is not None, "Client not initialised — use async context manager."
        bvids: List[str] = []
        pn = 1
        page_size = 20
        while len(bvids) < n:
            try:
                data = await self._get_json(BILIBILI_POPULAR, params={"pn": pn, "ps": page_size})
            except httpx.HTTPError as exc:
                logger.warning("Popular API page %d failed: %s", pn, exc)
                break
            if data.get("code") != 0:
                logger.warning(
                    "Popular API error code=%s: %s", data.get("code"), data.get("message")
                )
                break
            items: List[Dict[str, Any]] = (data.get("data") or {}).get("list") or []
            if not items:
                break
            for item in items:
                bvid = item.get("bvid")
                if bvid:
                    bvids.append(bvid)
                    if len(bvids) >= n:
                        break
            if (data.get("data") or {}).get("no_more"):
                break
            pn += 1
            await polite_delay()
        logger.info("Fetched %d trending BVIDs", len(bvids))
        return bvids[:n]

    async def crawl_bvids(self, bvids: List[str]) -> Dict[str, int]:
        """Crawl a list of BV numbers, up to _CONCURRENCY at a time."""
        totals: Dict[str, int] = {}
        sem = asyncio.Semaphore(_CONCURRENCY)

        async def _crawl_one(bvid: str) -> None:
            async with sem:
                logger.info("Processing %s", bvid)
                saved = 0
                try:
                    aid, cid, title = await self._resolve_bvid(bvid)
                    logger.info(
                        "  Resolved %s -> aid=%d cid=%d title=%r", bvid, aid, cid, title
                    )
                    video_url = f"https://www.bilibili.com/video/{bvid}"
                    saved += await self._crawl_comments(aid=aid, source_url=video_url)
                    saved += await self._crawl_danmaku(cid=cid, source_url=video_url)
                except httpx.HTTPError as exc:
                    logger.error("HTTP error for %s: %s", bvid, exc)
                except Exception as exc:
                    logger.exception("Unexpected error for %s: %s", bvid, exc)
                totals[bvid] = saved
                logger.info("  Total saved for %s: %d", bvid, saved)

        async with self:
            await asyncio.gather(*(_crawl_one(bvid) for bvid in bvids))

        return totals

    async def _resolve_bvid(self, bvid: str) -> Tuple[int, int, str]:
        data = await self._get_json(BILIBILI_VIDEO_INFO, params={"bvid": bvid})
        if data.get("code") != 0:
            raise ValueError(f"Bilibili API error for {bvid}: {data.get('message')}")
        video_data = data["data"]
        aid: int = video_data["aid"]
        cid: int = video_data["pages"][0]["cid"]
        title: str = video_data.get("title", "")
        await polite_delay()
        return aid, cid, title

    async def _crawl_comments(self, aid: int, source_url: str) -> int:
        total_saved = 0
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

            code = data.get("code")
            if code != 0:
                logger.warning(
                    "  API error on comment page %d: code=%s — "
                    "comments may require cookies (skipping)", page, code
                )
                break

            replies: List[Dict[str, Any]] = data.get("data", {}).get("replies") or []
            if not replies:
                logger.info("  No more comments on page %d", page)
                break

            page_saved = 0
            for reply in replies:
                content: str = reply.get("content", {}).get("message", "").strip()
                if content:
                    ts_raw = reply.get("ctime")
                    ts = datetime.fromtimestamp(ts_raw, tz=timezone.utc) if ts_raw else None
                    if await self.save_raw_text(
                        platform="bilibili",
                        content_type="comment",
                        raw_content=content,
                        source_url=source_url,
                        timestamp=ts,
                    ):
                        page_saved += 1

                for sub in (reply.get("replies") or []):
                    sub_content: str = sub.get("content", {}).get("message", "").strip()
                    if sub_content:
                        sub_ts_raw = sub.get("ctime")
                        sub_ts = (
                            datetime.fromtimestamp(sub_ts_raw, tz=timezone.utc)
                            if sub_ts_raw else None
                        )
                        if await self.save_raw_text(
                            platform="bilibili",
                            content_type="comment",
                            raw_content=sub_content,
                            source_url=source_url,
                            timestamp=sub_ts,
                        ):
                            page_saved += 1

            total_saved += page_saved
            logger.info("  Saved %d new texts from comment page %d", page_saved, page)
            await polite_delay()

        return total_saved

    async def _crawl_danmaku(self, cid: int, source_url: str) -> int:
        logger.info("  Fetching danmaku for cid=%d (cap=%d)", cid, self.max_danmaku)
        assert self.client is not None
        try:
            response = await self.client.get(BILIBILI_DANMAKU, params={"oid": cid})
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("  Danmaku fetch failed for cid=%d: %s", cid, exc)
            return 0

        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as exc:
            logger.warning("  Failed to parse danmaku XML: %s", exc)
            return 0

        saved = 0
        all_d = root.findall("d")
        logger.info("  Found %d danmaku entries, processing up to %d", len(all_d), self.max_danmaku)

        for d_elem in all_d[: self.max_danmaku]:
            text_content = (d_elem.text or "").strip()
            if not text_content:
                continue
            p_attr = d_elem.get("p", "")
            parts = p_attr.split(",")
            ts: Optional[datetime] = None
            if len(parts) >= 5:
                try:
                    ts = datetime.fromtimestamp(int(parts[4]), tz=timezone.utc)
                except (ValueError, OSError):
                    ts = None

            if await self.save_raw_text(
                platform="bilibili",
                content_type="danmaku",
                raw_content=text_content,
                source_url=source_url,
                timestamp=ts,
            ):
                saved += 1

        logger.info("  Saved %d new danmaku for cid=%d", saved, cid)
        await polite_delay()
        return saved


async def _main() -> None:
    parser = argparse.ArgumentParser(description="Bilibili crawler for 句式搜索引擎")
    parser.add_argument("--bvs", nargs="+", metavar="BVID", default=None,
                        help="One or more BV numbers to crawl")
    parser.add_argument(
        "--trending",
        type=int,
        metavar="N",
        default=None,
        help="Fetch and crawl the top N trending BVIDs from the Bilibili popular API",
    )
    parser.add_argument("--max-pages", type=int, default=5)
    parser.add_argument("--max-danmaku", type=int, default=300,
                        help="Max danmaku entries to save per video (default: 300)")
    args = parser.parse_args()

    if not args.bvs and not args.trending:
        parser.error("Provide --bvs, --trending, or both.")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    from app.database import AsyncSessionLocal

    crawler = BilibiliCrawler(
        session_factory=AsyncSessionLocal,
        max_pages=args.max_pages,
        max_danmaku=args.max_danmaku,
    )

    bvids: List[str] = list(args.bvs or [])
    if args.trending:
        async with crawler:
            trending_bvids = await crawler._fetch_trending_bvids(args.trending)
        seen = set(bvids)
        for bvid in trending_bvids:
            if bvid not in seen:
                bvids.append(bvid)
                seen.add(bvid)

    totals = await crawler.crawl_bvids(bvids)
    grand_total = sum(totals.values())
    logger.info("Crawl complete. Total saved: %d", grand_total)
    for bvid, n in totals.items():
        logger.info("  %s: %d", bvid, n)


if __name__ == "__main__":
    asyncio.run(_main())
