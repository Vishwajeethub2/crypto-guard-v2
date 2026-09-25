"""add email verification to users

Revision ID: c4e1a2b3d4e5
Revises: b35feb32c9eb
Create Date: 2026-09-25
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c4e1a2b3d4e5"
down_revision: Union[str, Sequence[str], None] = "92fd6171cf29"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "users",
        sa.Column(
            "is_email_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "verification_code_hash",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "verification_code_expires_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "verification_attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    # Existing accounts are treated as already verified.
    # New accounts use the model default of False.
    op.alter_column(
        "users",
        "is_email_verified",
        server_default=None,
    )

    op.alter_column(
        "users",
        "verification_attempts",
        server_default=None,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column(
        "users",
        "verification_attempts",
    )

    op.drop_column(
        "users",
        "verification_code_expires_at",
    )

    op.drop_column(
        "users",
        "verification_code_hash",
    )

    op.drop_column(
        "users",
        "is_email_verified",
    )