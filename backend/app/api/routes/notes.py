from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.case_model import Case
from app.db.note_model import CaseNote
from app.db.session import get_db
from app.schemas.note import (
    CaseNoteCreate,
    CaseNoteResponse,
    CaseNoteUpdate,
)
from app.services.auth import get_current_user


router = APIRouter(
    prefix="/cases",
    tags=["Case Notes"],
)


def get_owned_case(
    case_id: int,
    current_user,
    db: Session,
):
    case = (
        db.query(Case)
        .filter(
            Case.id == case_id,
            Case.created_by == current_user.id,
        )
        .first()
    )

    if case is None:
        raise HTTPException(
            status_code=404,
            detail="Case not found",
        )

    return case


@router.post(
    "/{case_id}/notes",
    response_model=CaseNoteResponse,
)
def create_case_note(
    case_id: int,
    note_data: CaseNoteCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    get_owned_case(
        case_id=case_id,
        current_user=current_user,
        db=db,
    )

    note = CaseNote(
        case_id=case_id,
        created_by=current_user.id,
        content=note_data.content.strip(),
    )

    db.add(note)
    db.commit()
    db.refresh(note)

    return note


@router.get(
    "/{case_id}/notes",
    response_model=list[CaseNoteResponse],
)
def get_case_notes(
    case_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    get_owned_case(
        case_id=case_id,
        current_user=current_user,
        db=db,
    )

    notes = (
        db.query(CaseNote)
        .filter(
            CaseNote.case_id == case_id,
        )
        .order_by(
            CaseNote.created_at.asc(),
            CaseNote.id.asc(),
        )
        .all()
    )

    return notes


@router.put(
    "/{case_id}/notes/{note_id}",
    response_model=CaseNoteResponse,
)
def update_case_note(
    case_id: int,
    note_id: int,
    note_data: CaseNoteUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    get_owned_case(
        case_id=case_id,
        current_user=current_user,
        db=db,
    )

    note = (
        db.query(CaseNote)
        .filter(
            CaseNote.id == note_id,
            CaseNote.case_id == case_id,
            CaseNote.created_by == current_user.id,
        )
        .first()
    )

    if note is None:
        raise HTTPException(
            status_code=404,
            detail="Note not found",
        )

    note.content = note_data.content.strip()

    db.commit()
    db.refresh(note)

    return note


@router.delete(
    "/{case_id}/notes/{note_id}",
)
def delete_case_note(
    case_id: int,
    note_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    get_owned_case(
        case_id=case_id,
        current_user=current_user,
        db=db,
    )

    note = (
        db.query(CaseNote)
        .filter(
            CaseNote.id == note_id,
            CaseNote.case_id == case_id,
            CaseNote.created_by == current_user.id,
        )
        .first()
    )

    if note is None:
        raise HTTPException(
            status_code=404,
            detail="Note not found",
        )

    db.delete(note)
    db.commit()

    return {
        "message": "Note deleted successfully",
        "note_id": note_id,
    }