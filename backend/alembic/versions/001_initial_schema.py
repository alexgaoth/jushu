"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Extensions ─────────────────────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")

    # ── raw_texts ──────────────────────────────────────────────────────────────
    op.create_table(
        "raw_texts",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("platform", sa.String(32), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_content", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(32), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default="false"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("content_hash", name="uq_raw_texts_content_hash"),
    )
    op.create_index("ix_raw_texts_content_hash", "raw_texts", ["content_hash"])
    op.create_index("ix_raw_texts_platform", "raw_texts", ["platform"])
    op.create_index("ix_raw_texts_processed", "raw_texts", ["processed"])

    # ── sentence_patterns ──────────────────────────────────────────────────────
    op.create_table(
        "sentence_patterns",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("template_text", sa.Text(), nullable=False),
        sa.Column("pos_sequence", sa.Text(), nullable=True),
        sa.Column("source_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("template_text", name="uq_sentence_patterns_template_text"),
    )
    op.create_index("ix_sentence_patterns_source_count", "sentence_patterns", ["source_count"])

    # GIN index for full-text search on template_text using to_tsvector (Chinese-compatible simple config)
    op.execute(
        """
        CREATE INDEX ix_sentence_patterns_template_fts
        ON sentence_patterns
        USING GIN (to_tsvector('simple', template_text))
        """
    )

    # Trigram index for LIKE / ILIKE search on template_text
    op.execute(
        """
        CREATE INDEX ix_sentence_patterns_template_trgm
        ON sentence_patterns
        USING GIN (template_text gin_trgm_ops)
        """
    )

    # ── pattern_examples ───────────────────────────────────────────────────────
    op.create_table(
        "pattern_examples",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("pattern_id", sa.BigInteger(), nullable=False),
        sa.Column("raw_text_id", sa.BigInteger(), nullable=True),
        sa.Column("slot_fillings", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["pattern_id"],
            ["sentence_patterns.id"],
            ondelete="CASCADE",
            name="fk_pattern_examples_pattern_id",
        ),
        sa.ForeignKeyConstraint(
            ["raw_text_id"],
            ["raw_texts.id"],
            ondelete="SET NULL",
            name="fk_pattern_examples_raw_text_id",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pattern_examples_pattern_id", "pattern_examples", ["pattern_id"])
    op.create_index("ix_pattern_examples_raw_text_id", "pattern_examples", ["raw_text_id"])

    # ── tags ───────────────────────────────────────────────────────────────────
    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_tags_name"),
    )
    op.create_index("ix_tags_category", "tags", ["category"])

    # ── pattern_tags ───────────────────────────────────────────────────────────
    op.create_table(
        "pattern_tags",
        sa.Column("pattern_id", sa.BigInteger(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["pattern_id"],
            ["sentence_patterns.id"],
            ondelete="CASCADE",
            name="fk_pattern_tags_pattern_id",
        ),
        sa.ForeignKeyConstraint(
            ["tag_id"],
            ["tags.id"],
            ondelete="CASCADE",
            name="fk_pattern_tags_tag_id",
        ),
        sa.PrimaryKeyConstraint("pattern_id", "tag_id"),
    )
    op.create_index("ix_pattern_tags_pattern_id", "pattern_tags", ["pattern_id"])
    op.create_index("ix_pattern_tags_tag_id", "pattern_tags", ["tag_id"])

    # ── search_logs ────────────────────────────────────────────────────────────
    op.create_table(
        "search_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("result_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_search_logs_created_at", "search_logs", ["created_at"])

    # ── updated_at auto-update trigger for sentence_patterns ───────────────────
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql'
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_sentence_patterns_updated_at
        BEFORE UPDATE ON sentence_patterns
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_sentence_patterns_updated_at ON sentence_patterns")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column")

    op.drop_table("search_logs")
    op.drop_table("pattern_tags")
    op.drop_table("tags")
    op.drop_table("pattern_examples")
    op.drop_table("sentence_patterns")
    op.drop_table("raw_texts")
