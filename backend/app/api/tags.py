from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Tag, PatternTag

router = APIRouter()


class TagWithCount(BaseModel):
    id: int
    name: str
    category: str
    pattern_count: int

    model_config = {"from_attributes": True}


class TagsResponse(BaseModel):
    total: int
    tags: List[TagWithCount]


@router.get("/tags", response_model=TagsResponse)
async def list_tags(db: AsyncSession = Depends(get_db)) -> TagsResponse:
    """
    Return all tags, each annotated with the number of patterns that carry it.
    """
    stmt = (
        select(
            Tag.id,
            Tag.name,
            Tag.category,
            func.count(PatternTag.pattern_id).label("pattern_count"),
        )
        .outerjoin(PatternTag, PatternTag.tag_id == Tag.id)
        .group_by(Tag.id)
        .order_by(Tag.category, Tag.name)
    )
    result = await db.execute(stmt)
    rows = result.all()

    tags = [
        TagWithCount(
            id=row.id,
            name=row.name,
            category=row.category,
            pattern_count=row.pattern_count or 0,
        )
        for row in rows
    ]
    return TagsResponse(total=len(tags), tags=tags)
