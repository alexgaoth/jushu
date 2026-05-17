"""pattern variants and example uniqueness

Revision ID: 002
Revises: 001
Create Date: 2026-05-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sentence_patterns",
        sa.Column("canonical_template_id", sa.BigInteger(), nullable=True),
    )
    op.create_foreign_key(
        "fk_sentence_patterns_canonical_template_id",
        "sentence_patterns",
        "sentence_patterns",
        ["canonical_template_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_sentence_patterns_canonical_template_id",
        "sentence_patterns",
        ["canonical_template_id"],
    )

    op.execute(
        """
        DELETE FROM pattern_examples pe
        USING pattern_examples dup
        WHERE pe.id > dup.id
          AND pe.pattern_id = dup.pattern_id
          AND pe.content = dup.content
        """
    )
    op.create_unique_constraint(
        "uq_pattern_example_content",
        "pattern_examples",
        ["pattern_id", "content"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_pattern_example_content", "pattern_examples", type_="unique")
    op.drop_index("ix_sentence_patterns_canonical_template_id", table_name="sentence_patterns")
    op.drop_constraint(
        "fk_sentence_patterns_canonical_template_id",
        "sentence_patterns",
        type_="foreignkey",
    )
    op.drop_column("sentence_patterns", "canonical_template_id")
