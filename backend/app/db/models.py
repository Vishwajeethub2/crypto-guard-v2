from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    full_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    is_email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    verification_code_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    verification_code_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    verification_attempts: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


# Import models so SQLAlchemy/Alembic registers them
# in the same metadata.
from app.db.case_model import Case
from app.db.wallet_model import Wallet
from app.db.note_model import CaseNote
from app.db.evidence_model import CaseEvidence
from app.db.bookmark_model import CaseBookmark
from app.db.report_model import CaseReport
