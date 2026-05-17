"""
Weibo crawler — fetches comment threads for posts surfaced by topic containers.

Usage (CLI):
    python -m crawlers.weibo --container-ids 102803_ctg1_7978_-_ctg1_7978
"""
import argparse
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Set

import httpx

from crawlers.base import BaseCrawler, polite_delay

logger = logging.getLogger(__name__)

WEIBO_TOPIC_CONTAINER = "https://m.weibo.cn/api/container/getIndex"
WEIBO_HOTFLOW_COMMENTS = "https://m.weibo.cn/comments/hotflow"


class WeiboCrawler(BaseCrawler):

    def __init__(
        self,
        session_factory: Any,
        max_pages: int = 5,
        comment_pages: Optional[int] = None,
    ) -> None:
        super().__init__(session_factory, max_pages)
        self.comment_pages = comment_pages or max_pages

    async def crawl(self) -> None:
        raise NotImplementedError("Call crawl_container_ids() directly.")

    async def crawl_container_ids(self, container_ids: List[str]) -> Dict[str, int]:
        totals: Dict[str, int] = {}

        async with self:
            for container_id in container_ids:
                logger.info("Processing Weibo container %s", container_id)
                saved = 0
                seen_posts: Set[str] = set()

                for page in range(1, self.max_pages + 1):
                    posts = await self._fetch_topic_posts(container_id, page)
                    if not posts:
                        break

                    page_saved = 0
                    for post in posts:
                        post_id = str(post.get("id") or "")
                        mid = str(post.get("mid") or post_id)
                        if not post_id or post_id in seen_posts:
                            continue
                        seen_posts.add(post_id)
                        source_url = f"https://m.weibo.cn/detail/{mid}"
                        page_saved += await self._crawl_post_comments(post_id, mid, source_url)

                    saved += page_saved
                    if page_saved == 0:
                        logger.info("  No new comment text found on page %d", page)
                    await polite_delay()

                totals[container_id] = saved
                logger.info("  Total saved for container %s: %d", container_id, saved)

        return totals

    async def _fetch_topic_posts(self, container_id: str, page: int) -> List[Dict[str, Any]]:
        try:
            data = await self._get_json(
                WEIBO_TOPIC_CONTAINER,
                params={"containerid": container_id, "page": page},
            )
        except httpx.HTTPError as exc:
            logger.warning("Topic fetch failed for container %s page %d: %s", container_id, page, exc)
            return []

        cards = (data.get("data") or {}).get("cards") or []
        posts = [post for post in self._iter_mblogs(cards) if isinstance(post, dict)]
        logger.info("  Topic page %d yielded %d post(s)", page, len(posts))
        return posts

    def _iter_mblogs(self, cards: Iterable[Dict[str, Any]]) -> Iterable[Dict[str, Any]]:
        for card in cards:
            if not isinstance(card, dict):
                continue
            mblog = card.get("mblog")
            if isinstance(mblog, dict):
                yield mblog
            card_group = card.get("card_group") or []
            for nested in self._iter_mblogs(card_group):
                yield nested

    async def _crawl_post_comments(self, post_id: str, mid: str, source_url: str) -> int:
        total_saved = 0
        max_id = 0

        for page in range(1, self.comment_pages + 1):
            logger.info("  Fetching comments page %d for post=%s", page, post_id)
            try:
                data = await self._get_json(
                    WEIBO_HOTFLOW_COMMENTS,
                    params={
                        "id": post_id,
                        "mid": mid,
                        "max_id": max_id,
                        "max_id_type": 0,
                    },
                )
            except httpx.HTTPError as exc:
                logger.warning("  Comment fetch failed for post %s page %d: %s", post_id, page, exc)
                break

            payload = data.get("data") or {}
            comments = payload.get("data") or []
            if not comments:
                break

            page_saved = 0
            for comment in comments:
                page_saved += await self._save_comment_tree(comment, source_url)

            total_saved += page_saved
            logger.info("  Saved %d new texts from post page %d", page_saved, page)

            next_max_id = payload.get("max_id")
            if next_max_id in (None, 0):
                break
            max_id = next_max_id
            await polite_delay()

        return total_saved

    async def _save_comment_tree(self, comment: Dict[str, Any], source_url: str) -> int:
        saved = 0
        content = (comment.get("text") or "").strip()
        timestamp = self._parse_timestamp(comment.get("created_at"))
        if content:
            if await self.save_raw_text(
                platform="weibo",
                content_type="comment",
                raw_content=content,
                source_url=source_url,
                timestamp=timestamp,
            ):
                saved += 1

        for child in comment.get("comments") or []:
            if isinstance(child, dict):
                saved += await self._save_comment_tree(child, source_url)

        return saved

    def _parse_timestamp(self, raw_value: Any) -> Optional[datetime]:
        if not isinstance(raw_value, str):
            return None
        try:
            return datetime.strptime(raw_value, "%a %b %d %H:%M:%S %z %Y")
        except ValueError:
            return None


async def _main() -> None:
    parser = argparse.ArgumentParser(description="Weibo crawler for topic comment streams")
    parser.add_argument(
        "--container-ids",
        nargs="+",
        metavar="CID",
        default=None,
        help="Weibo topic container IDs to crawl",
    )
    parser.add_argument("--max-pages", type=int, default=5)
    parser.add_argument(
        "--comment-pages",
        type=int,
        default=3,
        help="Maximum comment pages to fetch per surfaced post (default: 3)",
    )
    args = parser.parse_args()

    if not args.container_ids:
        parser.error("Provide at least one --container-ids value.")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    from app.database import AsyncSessionLocal

    crawler = WeiboCrawler(
        session_factory=AsyncSessionLocal,
        max_pages=args.max_pages,
        comment_pages=args.comment_pages,
    )

    totals = await crawler.crawl_container_ids(args.container_ids)
    grand_total = sum(totals.values())
    logger.info("Crawl complete. Total saved: %d", grand_total)
    for container_id, saved in totals.items():
        logger.info("  %s: %d", container_id, saved)


if __name__ == "__main__":
    asyncio.run(_main())
