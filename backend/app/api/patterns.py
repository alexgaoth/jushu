import re
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import SentencePattern, PatternExample, Tag, PatternTag

router = APIRouter()


# ── Response Schemas ──────────────────────────────────────────────────────────

class TagOut(BaseModel):
    id: int
    name: str
    category: str
    model_config = {"from_attributes": True}


class ExampleOut(BaseModel):
    id: int
    content: str
    slot_fillings: Optional[Dict[str, Any]] = None
    model_config = {"from_attributes": True}


class PatternDetail(BaseModel):
    id: int
    template_text: str
    pos_sequence: Optional[str]
    source_count: int
    example_count: int
    tags: List[TagOut]
    examples: List[ExampleOut]
    model_config = {"from_attributes": True}


class GenerateResponse(BaseModel):
    template_text: str
    result: str
    filled_slots: Dict[str, str]


class ExamplesPageResponse(BaseModel):
    total: int
    page: int
    size: int
    results: List[ExampleOut]


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/patterns/{pattern_id}", response_model=PatternDetail)
async def get_pattern(
    pattern_id: int,
    db: AsyncSession = Depends(get_db),
) -> PatternDetail:
    """Return full detail for a single pattern, including examples and tags."""
    stmt = (
        select(SentencePattern)
        .where(SentencePattern.id == pattern_id)
        .options(
            selectinload(SentencePattern.pattern_tags).selectinload(PatternTag.tag),
            selectinload(SentencePattern.examples),
        )
    )
    result = await db.execute(stmt)
    pattern = result.scalar_one_or_none()
    if pattern is None:
        raise HTTPException(status_code=404, detail="Pattern not found")

    tags = [
        TagOut(id=pt.tag.id, name=pt.tag.name, category=pt.tag.category)
        for pt in pattern.pattern_tags
    ]
    examples = [
        ExampleOut(id=e.id, content=e.content, slot_fillings=e.slot_fillings)
        for e in pattern.examples
    ]
    return PatternDetail(
        id=pattern.id,
        template_text=pattern.template_text,
        pos_sequence=pattern.pos_sequence,
        source_count=pattern.source_count,
        example_count=len(pattern.examples),
        tags=tags,
        examples=examples,
    )


@router.get("/patterns/{pattern_id}/generate", response_model=GenerateResponse)
async def generate_from_pattern(
    request: Request,
    pattern_id: int,
    db: AsyncSession = Depends(get_db),
) -> GenerateResponse:
    """
    Fill slot placeholders in the pattern template.
    All query parameters are treated as slot key-value pairs.

    Example:
        GET /api/patterns/42/generate?slot1=小明&slot2=跑步
    """
    stmt = select(SentencePattern).where(SentencePattern.id == pattern_id)
    result = await db.execute(stmt)
    pattern = result.scalar_one_or_none()
    if pattern is None:
        raise HTTPException(status_code=404, detail="Pattern not found")

    # Collect slot values from all query params
    slot_values: Dict[str, str] = dict(request.query_params)

    # Find all slot names declared in the template
    slot_names = re.findall(r"\{(\w+)\}", pattern.template_text)
    missing = [s for s in slot_names if s not in slot_values]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Missing slot values for: {missing}. Template requires: {slot_names}",
        )

    filled = pattern.template_text
    for slot in slot_names:
        filled = filled.replace(f"{{{slot}}}", slot_values[slot])

    return GenerateResponse(
        template_text=pattern.template_text,
        result=filled,
        filled_slots={k: slot_values[k] for k in slot_names if k in slot_values},
    )


@router.get("/examples", response_model=ExamplesPageResponse)
async def list_examples(
    pattern_id: int = Query(..., description="ID of the parent pattern"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort: str = Query("hot", pattern="^(hot|new)$"),
    db: AsyncSession = Depends(get_db),
) -> ExamplesPageResponse:
    """
    Paginated list of examples for a pattern.

    sort=hot  -> ordered by example id ascending (insertion order, proxy for stability)
    sort=new  -> ordered by created_at descending (most recent first)
    """
    # Verify pattern exists
    pat_stmt = select(SentencePattern.id).where(SentencePattern.id == pattern_id)
    pat_result = await db.execute(pat_stmt)
    if pat_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Pattern not found")

    offset = (page - 1) * size

    count_stmt = (
        select(func.count())
        .select_from(PatternExample)
        .where(PatternExample.pattern_id == pattern_id)
    )
    total = (await db.execute(count_stmt)).scalar_one()

    order_col = (
        PatternExample.created_at.desc()
        if sort == "new"
        else PatternExample.id.asc()
    )

    stmt = (
        select(PatternExample)
        .where(PatternExample.pattern_id == pattern_id)
        .order_by(order_col)
        .offset(offset)
        .limit(size)
    )
    result = await db.execute(stmt)
    examples = result.scalars().all()

    return ExamplesPageResponse(
        total=total,
        page=page,
        size=size,
        results=[
            ExampleOut(id=e.id, content=e.content, slot_fillings=e.slot_fillings)
            for e in examples
        ],
    )
