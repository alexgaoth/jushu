from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import SentencePattern, PatternExample, Tag, PatternTag, SearchLog

router = APIRouter()


# ── Response Schemas ──────────────────────────────────────────────────────────

class TagOut(BaseModel):
    id: int
    name: str
    category: str

    model_config = {"from_attributes": True}


class PatternSummary(BaseModel):
    id: int
    template_text: str
    source_count: int
    example_count: int
    example: Optional[str] = None
    tags: List[TagOut] = []

    model_config = {"from_attributes": True}


class SearchResponse(BaseModel):
    total: int
    page: int
    size: int
    results: List[PatternSummary]


class TrendingResponse(BaseModel):
    range: str
    results: List[PatternSummary]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _wildcard_to_sql(q: str) -> str:
    """Convert user-facing wildcard * to SQL LIKE % wildcard."""
    # Escape existing SQL special chars first
    escaped = q.replace("%", r"\%").replace("_", r"\_")
    return escaped.replace("*", "%")


async def _log_search(db: AsyncSession, query: str, result_count: int) -> None:
    log = SearchLog(query=query, result_count=result_count)
    db.add(log)
    # commit handled by get_db dependency


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/search", response_model=SearchResponse)
async def search_patterns(
    q: str = Query("", min_length=0, description="Search query, supports * wildcard"),
    tag: Optional[str] = Query(None, description="Filter by exact tag name"),
    sort: str = Query("usage", pattern="^(usage|newest|examples)$"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """
    Search sentence patterns by template text.
    Wildcard * is supported (maps to SQL ILIKE %).
    Falls back to PostgreSQL full-text search when no wildcard is present.
    """
    offset = (page - 1) * size
    filters = []

    if q.strip():
        sql_pattern = _wildcard_to_sql(q)
        has_wildcard = "%" in sql_pattern

        if has_wildcard:
            filters.append(
                SentencePattern.template_text.ilike(sql_pattern, escape="\\")
            )
        else:
            filters.append(
                or_(
                    SentencePattern.template_text.ilike(f"%{q}%"),
                    SentencePattern.id.in_(
                        select(PatternExample.pattern_id).where(
                            PatternExample.content.ilike(f"%{q}%")
                        )
                    ),
                )
            )

    if tag:
        filters.append(
            SentencePattern.pattern_tags.any(
                PatternTag.tag.has(Tag.name == tag)
            )
        )

    example_count_subquery = (
        select(func.count(PatternExample.id))
        .where(PatternExample.pattern_id == SentencePattern.id)
        .correlate(SentencePattern)
        .scalar_subquery()
    )
    order_by_map = {
        "usage": SentencePattern.source_count.desc(),
        "newest": SentencePattern.created_at.desc(),
        "examples": example_count_subquery.desc(),
    }
    order_by_clause = order_by_map[sort]

    # Count query
    count_stmt = select(func.count()).select_from(SentencePattern)
    if filters:
        count_stmt = count_stmt.where(*filters)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # Main query with eager loading
    stmt = (
        select(SentencePattern)
        .options(
            selectinload(SentencePattern.pattern_tags).selectinload(PatternTag.tag),
            selectinload(SentencePattern.examples),
        )
        .order_by(order_by_clause)
        .offset(offset)
        .limit(size)
    )
    if filters:
        stmt = stmt.where(*filters)
    result = await db.execute(stmt)
    patterns = result.scalars().all()

    summaries: List[PatternSummary] = []
    for p in patterns:
        # Pick first example
        first_example = p.examples[0].content if p.examples else None
        tags = [TagOut(id=pt.tag.id, name=pt.tag.name, category=pt.tag.category) for pt in p.pattern_tags]
        summaries.append(
            PatternSummary(
                id=p.id,
                template_text=p.template_text,
                source_count=p.source_count,
                example_count=len(p.examples),
                example=first_example,
                tags=tags,
            )
        )

    await _log_search(db, q, total)

    return SearchResponse(total=total, page=page, size=size, results=summaries)


@router.get("/trending", response_model=TrendingResponse)
async def trending_patterns(
    range: str = Query("week", pattern="^(day|week|month|all)$"),
    db: AsyncSession = Depends(get_db),
) -> TrendingResponse:
    """Return top patterns by source_count, optionally filtered by recent creation date."""
    now = datetime.now(timezone.utc)
    range_map = {
        "day": now - timedelta(days=1),
        "week": now - timedelta(weeks=1),
        "month": now - timedelta(days=30),
        "all": None,
    }
    since = range_map.get(range)

    stmt = (
        select(SentencePattern)
        .options(
            selectinload(SentencePattern.pattern_tags).selectinload(PatternTag.tag),
            selectinload(SentencePattern.examples),
        )
        .order_by(SentencePattern.source_count.desc())
        .limit(20)
    )
    if since is not None:
        stmt = stmt.where(SentencePattern.updated_at >= since)

    result = await db.execute(stmt)
    patterns = result.scalars().all()

    summaries: List[PatternSummary] = []
    for p in patterns:
        first_example = p.examples[0].content if p.examples else None
        tags = [TagOut(id=pt.tag.id, name=pt.tag.name, category=pt.tag.category) for pt in p.pattern_tags]
        summaries.append(
            PatternSummary(
                id=p.id,
                template_text=p.template_text,
                source_count=p.source_count,
                example_count=len(p.examples),
                example=first_example,
                tags=tags,
            )
        )

    return TrendingResponse(range=range, results=summaries)
