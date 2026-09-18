from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import mapped_column

from app.db.models import Base


class CaseReport(Base):
    __tablename__ = "case_reports"

    id = mapped_column(Integer, primary_key=True, index=True)

    case_id = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_by = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    report_type = mapped_column(
        String(50),
        nullable=False,
        default="investigation",
    )

    file_name = mapped_column(
        String(255),
        nullable=False,
    )

    status = mapped_column(
        String(30),
        nullable=False,
        default="generated",
    )

    created_at = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )