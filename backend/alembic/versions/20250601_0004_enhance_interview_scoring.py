"""enhance interview scoring and adaptive fields

Revision ID: 20250601_0004
Revises: 20250601_0003
Create Date: 2025-06-01 18:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20250601_0004"
down_revision: Union[str, None] = "20250601_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "interview_sessions",
        sa.Column("current_difficulty", sa.String(length=20), nullable=False, server_default="easy"),
    )
    op.add_column(
        "interview_sessions",
        sa.Column("readiness_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "interview_sessions",
        sa.Column("weaknesses", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "interview_sessions",
        sa.Column("terminated_early", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "interview_sessions",
        sa.Column("termination_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "interview_sessions",
        sa.Column("performance_breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.add_column(
        "interview_questions",
        sa.Column("difficulty", sa.String(length=20), nullable=False, server_default="easy"),
    )

    op.add_column("interview_answers", sa.Column("score", sa.Float(), nullable=True))
    op.add_column("interview_answers", sa.Column("feedback", sa.Text(), nullable=True))
    op.add_column(
        "interview_answers",
        sa.Column("score_breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("interview_answers", "score_breakdown")
    op.drop_column("interview_answers", "feedback")
    op.drop_column("interview_answers", "score")
    op.drop_column("interview_questions", "difficulty")
    op.drop_column("interview_sessions", "performance_breakdown")
    op.drop_column("interview_sessions", "termination_reason")
    op.drop_column("interview_sessions", "terminated_early")
    op.drop_column("interview_sessions", "weaknesses")
    op.drop_column("interview_sessions", "readiness_score")
    op.drop_column("interview_sessions", "current_difficulty")
