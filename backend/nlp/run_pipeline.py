"""
NLP pipeline: read raw_texts -> extract patterns -> upsert sentence_patterns
              -> create pattern_examples -> assign tags.

Usage:
    python -m nlp.run_pipeline                   # process all unprocessed texts
    python -m nlp.run_pipeline --since yesterday  # texts created since yesterday
    python -m nlp.run_pipeline --since 2026-05-01 # texts created since a date

The pipeline tracks which raw_texts have been processed via the `processed`
boolean flag, so it is safe to re-run without creating duplicate records.
"""
import argparse
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

CHUNK = 100


# ── Date parsing helper ───────────────────────────────────────────────────────

def _parse_since(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    value = value.strip().lower()
    if value == "yesterday":
        return (datetime.now(timezone.utc) - timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    if value == "today":
        return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            dt = datetime.strptime(value, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {value!r}")


# ── Core pipeline ─────────────────────────────────────────────────────────────

async def process_text(db: AsyncSession, raw_text) -> int:
    """
    Extract patterns from one RawText record and persist results.
    Returns the number of new pattern records created.
    """
    from nlp.extractor import extract
    from nlp.tagger import assign_tags, get_tag_category
    from app.models import SentencePattern, PatternExample, Tag, PatternTag

    extractions = extract(raw_text.raw_content)
    new_count = 0

    for extraction in extractions:
        template = extraction.template
        slot_fillings = extraction.slot_fillings
        pos_sequence = extraction.pos_sequence

        # Upsert SentencePattern by template_text (unique constraint)
        result = await db.execute(
            select(SentencePattern).where(SentencePattern.template_text == template)
        )
        pattern = result.scalar_one_or_none()

        if pattern is None:
            pattern = SentencePattern(
                template_text=template,
                pos_sequence=pos_sequence,
                source_count=1,
            )
            db.add(pattern)
            await db.flush()  # populate pattern.id
            new_count += 1
            logger.debug("New pattern: %r", template)
        else:
            pattern.source_count += 1

        # Build example content: fill slots into template
        example_content = template
        for slot_key, slot_val in slot_fillings.items():
            example_content = example_content.replace(f"{{{slot_key}}}", slot_val)

        example = PatternExample(
            pattern_id=pattern.id,
            raw_text_id=raw_text.id,
            slot_fillings=slot_fillings if slot_fillings else None,
            content=example_content,
        )
        db.add(example)

        # Assign tags
        tag_names = assign_tags(template, example_content)
        for tag_name in tag_names:
            tag_result = await db.execute(select(Tag).where(Tag.name == tag_name))
            tag = tag_result.scalar_one_or_none()
            if tag is None:
                tag = Tag(name=tag_name, category=get_tag_category(tag_name))
                db.add(tag)
                await db.flush()

            await db.execute(
                pg_insert(PatternTag)
                .values(pattern_id=pattern.id, tag_id=tag.id)
                .on_conflict_do_nothing()
            )

    raw_text.processed = True
    return new_count


async def run_pipeline(since: Optional[datetime] = None) -> None:
    from app.database import AsyncSessionLocal
    from app.models import RawText

    logger.info("Starting NLP pipeline (since=%s)", since)
    total_processed = 0
    total_new_patterns = 0

    while True:
        # Load one chunk of IDs so no objects are held across sessions
        async with AsyncSessionLocal() as db:
            stmt = select(RawText.id).where(RawText.processed == False)  # noqa: E712
            if since is not None:
                stmt = stmt.where(RawText.created_at >= since)
            stmt = stmt.order_by(RawText.created_at.asc()).limit(CHUNK)
            result = await db.execute(stmt)
            chunk_ids: List[int] = list(result.scalars().all())

        if not chunk_ids:
            break

        logger.info("Processing chunk of %d unprocessed raw text(s).", len(chunk_ids))

        for raw_text_id in chunk_ids:
            try:
                async with AsyncSessionLocal() as db:
                    result = await db.execute(
                        select(RawText).where(RawText.id == raw_text_id)
                    )
                    raw_text = result.scalar_one()
                    new_patterns = await process_text(db, raw_text)
                    await db.commit()
                total_new_patterns += new_patterns
                total_processed += 1
            except Exception as exc:
                logger.error(
                    "Error processing raw_text id=%d: %s", raw_text_id, exc, exc_info=True
                )
                # Quarantine the broken record so it is not retried forever
                try:
                    async with AsyncSessionLocal() as db:
                        result = await db.execute(
                            select(RawText).where(RawText.id == raw_text_id)
                        )
                        rt = result.scalar_one_or_none()
                        if rt is not None:
                            rt.processed = True
                            await db.commit()
                except Exception as inner_exc:
                    logger.error(
                        "Failed to quarantine raw_text id=%d: %s", raw_text_id, inner_exc
                    )

    logger.info(
        "Pipeline complete: %d texts processed, %d new patterns created.",
        total_processed,
        total_new_patterns,
    )


# ── CLI entry point ───────────────────────────────────────────────────────────

def _main() -> None:
    parser = argparse.ArgumentParser(
        description="NLP pipeline: extract patterns from raw_texts and persist to DB."
    )
    parser.add_argument(
        "--since",
        metavar="DATE",
        default=None,
        help=(
            "Only process raw_texts created since this date. "
            "Accepts 'yesterday', 'today', or ISO date (YYYY-MM-DD). "
            "Defaults to all unprocessed texts."
        ),
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    since_dt = _parse_since(args.since) if args.since else None
    asyncio.run(run_pipeline(since=since_dt))


if __name__ == "__main__":
    _main()
