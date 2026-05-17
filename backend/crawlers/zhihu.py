"""
Zhihu crawler — fetches comment threads under answers for selected questions.

Usage (CLI):
    python -m crawlers.zhihu --question-ids 123456789 987654321
    python -m crawlers.zhihu --answer-ids 1122334455 9988776655
    python -m crawlers.zhihu --question-ids 123456789 --answer-ids 1122334455
"""
import argparse
import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from crawlers.base import BaseCrawler, polite_delay

logger = logging.getLogger(__name__)

ZHIHU_QUESTION_ANSWERS = "https://www.zhihu.com/api/v4/questions/{question_id}/answers"
ZHIHU_ANSWER_COMMENTS = "https://www.zhihu.com/api/v4/answers/{answer_id}/comments"


class ZhihuCrawler(BaseCrawler):

    def __init__(
        self,
        session_factory: Any,
        max_pages: int = 5,
        answers_per_question: int = 20,
    ) -> None:
        super().__init__(session_factory, max_pages)
        self.answers_per_question = answers_per_question

    async def crawl(self) -> None:
        raise NotImplementedError("Call crawl_question_ids() or crawl_answer_ids() directly.")

    async def crawl_question_ids(self, question_ids: List[int]) -> Dict[str, int]:
        totals: Dict[str, int] = {}
        async with self:
            for question_id in question_ids:
                saved = 0
                logger.info("Processing Zhihu question %s", question_id)
                answers = await self._fetch_answers(question_id, self.answers_per_question)
                for answer in answers:
                    answer_id = answer.get("id")
                    if answer_id is None:
                        continue
                    source_url = f"https://www.zhihu.com/question/{question_id}/answer/{answer_id}"
                    saved += await self._crawl_answer_comments(answer_id, source_url)
                totals[str(question_id)] = saved
                logger.info("  Total saved for question %s: %d", question_id, saved)
        return totals

    async def crawl_answer_ids(self, answer_ids: List[int]) -> Dict[str, int]:
        totals: Dict[str, int] = {}
        async with self:
            for answer_id in answer_ids:
                logger.info("Processing Zhihu answer %s", answer_id)
                source_url = f"https://www.zhihu.com/answer/{answer_id}"
                saved = await self._crawl_answer_comments(answer_id, source_url)
                totals[str(answer_id)] = saved
                logger.info("  Total saved for answer %s: %d", answer_id, saved)
        return totals

    async def _fetch_answers(self, question_id: int, limit: int) -> List[Dict[str, Any]]:
        assert self.client is not None, "Client not initialised — use async context manager."
        answers: List[Dict[str, Any]] = []
        offset = 0
        page_size = 20

        while len(answers) < limit and offset < self.max_pages * page_size:
            try:
                data = await self._get_json(
                    ZHIHU_QUESTION_ANSWERS.format(question_id=question_id),
                    params={
                        "limit": min(page_size, limit - len(answers)),
                        "offset": offset,
                    },
                )
            except httpx.HTTPError as exc:
                logger.warning("Answer fetch failed for question %s: %s", question_id, exc)
                break

            items = data.get("data") or []
            if not items:
                break

            answers.extend(item for item in items if isinstance(item, dict))
            paging = data.get("paging") or {}
            if paging.get("is_end"):
                break

            offset += len(items)
            await polite_delay()

        logger.info("Fetched %d answer(s) for question %s", len(answers), question_id)
        return answers[:limit]

    async def _crawl_answer_comments(self, answer_id: int, source_url: str) -> int:
        total_saved = 0
        offset = 0
        page_size = 20

        for page in range(1, self.max_pages + 1):
            logger.info("  Fetching answer comments page %d for answer=%s", page, answer_id)
            try:
                data = await self._get_json(
                    ZHIHU_ANSWER_COMMENTS.format(answer_id=answer_id),
                    params={"limit": page_size, "offset": offset},
                )
            except httpx.HTTPError as exc:
                logger.warning("  Comment fetch failed for answer %s page %d: %s", answer_id, page, exc)
                break

            comments = data.get("data") or []
            if not comments:
                break

            page_saved = 0
            for comment in comments:
                page_saved += await self._save_comment_tree(comment, source_url)

            total_saved += page_saved
            logger.info("  Saved %d new texts from answer page %d", page_saved, page)

            paging = data.get("paging") or {}
            if paging.get("is_end"):
                break
            offset += len(comments)
            await polite_delay()

        return total_saved

    async def _save_comment_tree(self, comment: Dict[str, Any], source_url: str) -> int:
        saved = 0
        content = (comment.get("content") or "").strip()
        timestamp = self._parse_timestamp(comment.get("created_time"))
        if content:
            if await self.save_raw_text(
                platform="zhihu",
                content_type="comment",
                raw_content=content,
                source_url=source_url,
                timestamp=timestamp,
            ):
                saved += 1

        for child in comment.get("child_comments") or []:
            if isinstance(child, dict):
                saved += await self._save_comment_tree(child, source_url)

        return saved

    def _parse_timestamp(self, raw_value: Any) -> Optional[datetime]:
        if isinstance(raw_value, (int, float)):
            try:
                return datetime.fromtimestamp(raw_value, tz=timezone.utc)
            except (ValueError, OSError):
                return None
        return None


async def _main() -> None:
    parser = argparse.ArgumentParser(description="Zhihu crawler for answer comment threads")
    parser.add_argument(
        "--question-ids",
        nargs="+",
        type=int,
        metavar="QID",
        default=None,
        help="Zhihu question IDs to crawl via answer comment threads",
    )
    parser.add_argument(
        "--answer-ids",
        nargs="+",
        type=int,
        metavar="AID",
        default=None,
        help="Zhihu answer IDs whose comment threads should be crawled directly",
    )
    parser.add_argument("--max-pages", type=int, default=5)
    parser.add_argument(
        "--answers-per-question",
        type=int,
        default=20,
        help="Maximum answers to crawl per question (default: 20)",
    )
    args = parser.parse_args()

    if not args.question_ids and not args.answer_ids:
        parser.error("Provide --question-ids, --answer-ids, or both.")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    from app.database import AsyncSessionLocal

    crawler = ZhihuCrawler(
        session_factory=AsyncSessionLocal,
        max_pages=args.max_pages,
        answers_per_question=args.answers_per_question,
    )

    totals: Dict[str, int] = {}
    if args.question_ids:
        totals.update(await crawler.crawl_question_ids(args.question_ids))
    if args.answer_ids:
        totals.update(await crawler.crawl_answer_ids(args.answer_ids))

    grand_total = sum(totals.values())
    logger.info("Crawl complete. Total saved: %d", grand_total)
    for key, saved in totals.items():
        logger.info("  %s: %d", key, saved)


if __name__ == "__main__":
    asyncio.run(_main())
