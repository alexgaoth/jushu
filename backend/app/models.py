from datetime import datetime
from typing import Optional
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base


class RawText(Base):
    __tablename__ = "raw_texts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    platform: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="bilibili/weibo/zhihu/tieba"
    )
    timestamp: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Original content timestamp"
    )
    raw_content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="comment/danmaku/post"
    )
    content_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, comment="SHA-256 of raw_content"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    pattern_examples: Mapped[list["PatternExample"]] = relationship(
        "PatternExample", back_populates="raw_text"
    )

    __table_args__ = (
        Index("ix_raw_texts_content_hash", "content_hash"),
        Index("ix_raw_texts_platform", "platform"),
        Index("ix_raw_texts_processed", "processed"),
    )


class SentencePattern(Base):
    __tablename__ = "sentence_patterns"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    template_text: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    canonical_template_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("sentence_patterns.id", ondelete="SET NULL"),
        nullable=True,
        comment="Canonical parent template for subvariants",
    )
    pos_sequence: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="POS tag sequence, space-separated"
    )
    source_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Number of source texts"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    examples: Mapped[list["PatternExample"]] = relationship(
        "PatternExample", back_populates="pattern", cascade="all, delete-orphan"
    )
    canonical_template: Mapped[Optional["SentencePattern"]] = relationship(
        "SentencePattern",
        remote_side="SentencePattern.id",
        back_populates="variants",
        foreign_keys=[canonical_template_id],
    )
    variants: Mapped[list["SentencePattern"]] = relationship(
        "SentencePattern",
        back_populates="canonical_template",
        foreign_keys=[canonical_template_id],
    )
    pattern_tags: Mapped[list["PatternTag"]] = relationship(
        "PatternTag", back_populates="pattern", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_sentence_patterns_canonical_template_id", "canonical_template_id"),
        Index("ix_sentence_patterns_source_count", "source_count"),
        # GIN index for full-text search will be added in migration
    )


class PatternExample(Base):
    __tablename__ = "pattern_examples"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    pattern_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sentence_patterns.id", ondelete="CASCADE"), nullable=False
    )
    raw_text_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("raw_texts.id", ondelete="SET NULL"), nullable=True
    )
    slot_fillings: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, comment="Map of slot name -> filled value"
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Full resolved example sentence"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    pattern: Mapped["SentencePattern"] = relationship(
        "SentencePattern", back_populates="examples"
    )
    raw_text: Mapped[Optional["RawText"]] = relationship(
        "RawText", back_populates="pattern_examples"
    )

    __table_args__ = (
        UniqueConstraint("pattern_id", "content", name="uq_pattern_example_content"),
        Index("ix_pattern_examples_pattern_id", "pattern_id"),
        Index("ix_pattern_examples_raw_text_id", "raw_text_id"),
    )


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    category: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="domain/sentiment/style"
    )

    # Relationships
    pattern_tags: Mapped[list["PatternTag"]] = relationship(
        "PatternTag", back_populates="tag", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_tags_category", "category"),)


class PatternTag(Base):
    __tablename__ = "pattern_tags"

    pattern_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("sentence_patterns.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    tag_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    # Relationships
    pattern: Mapped["SentencePattern"] = relationship(
        "SentencePattern", back_populates="pattern_tags"
    )
    tag: Mapped["Tag"] = relationship("Tag", back_populates="pattern_tags")

    __table_args__ = (
        Index("ix_pattern_tags_tag_id", "tag_id"),
        Index("ix_pattern_tags_pattern_id", "pattern_id"),
    )


class SearchLog(Base):
    __tablename__ = "search_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    result_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (Index("ix_search_logs_created_at", "created_at"),)
