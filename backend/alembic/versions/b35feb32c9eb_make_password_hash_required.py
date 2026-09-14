"""make password hash required

Revision ID: b35feb32c9eb
Revises: a2105e1aaf83
Create Date: 2026-09-14
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b35feb32c9eb"
down_revision: Union[str, Sequence[str], None] = "a2105e1aaf83"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "users",
        "password_hash",
        nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "users",
        "password_hash",
        nullable=True,
    )