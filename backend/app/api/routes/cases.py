from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.case_model import Case
from app.db.session import get_db
from app.schemas.case import CaseCreate
from app.services.auth import get_current_user


router = APIRouter(prefix="/cases", tags=["Cases"])


@router.post("/")
def create_case(
    case_data: CaseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    case = Case(
        title=case_data.title,
        description=case_data.description,
        created_by=current_user.id,
    )

    db.add(case)
    db.commit()
    db.refresh(case)

    return {
        "id": case.id,
        "title": case.title,
        "description": case.description,
        "status": case.status,
        "created_by": case.created_by,
        "created_at": case.created_at,
    }