from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.bookmark_model import CaseBookmark
from app.db.case_model import Case
from app.db.session import get_db
from app.schemas.bookmark import (
    CaseBookmarkCreate,
    CaseBookmarkResponse,
    CaseBookmarkUpdate,
)
from app.services.auth import get_current_user


router = APIRouter(
    prefix="/cases",
    tags=["Case Bookmarks"],
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
    "/{case_id}/bookmarks",
    response_model=CaseBookmarkResponse,
)
def create_case_bookmark(
    case_id: int,
    bookmark_data: CaseBookmarkCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    get_owned_case(
        case_id=case_id,
        current_user=current_user,
        db=db,
    )

    bookmark = CaseBookmark(
        case_id=case_id,
        created_by=current_user.id,
        bookmark_type=bookmark_data.bookmark_type.strip(),
        title=bookmark_data.title.strip(),
        reference=bookmark_data.reference.strip(),
    )

    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)

    return bookmark


@router.get(
    "/{case_id}/bookmarks",
    response_model=list[CaseBookmarkResponse],
)
def get_case_bookmarks(
    case_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    get_owned_case(
        case_id=case_id,
        current_user=current_user,
        db=db,
    )

    bookmarks = (
        db.query(CaseBookmark)
        .filter(
            CaseBookmark.case_id == case_id,
        )
        .order_by(
            CaseBookmark.created_at.asc(),
            CaseBookmark.id.asc(),
        )
        .all()
    )

    return bookmarks


@router.put(
    "/{case_id}/bookmarks/{bookmark_id}",
    response_model=CaseBookmarkResponse,
)
def update_case_bookmark(
    case_id: int,
    bookmark_id: int,
    bookmark_data: CaseBookmarkUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    get_owned_case(
        case_id=case_id,
        current_user=current_user,
        db=db,
    )

    bookmark = (
        db.query(CaseBookmark)
        .filter(
            CaseBookmark.id == bookmark_id,
            CaseBookmark.case_id == case_id,
            CaseBookmark.created_by == current_user.id,
        )
        .first()
    )

    if bookmark is None:
        raise HTTPException(
            status_code=404,
            detail="Bookmark not found",
        )

    if bookmark_data.bookmark_type is not None:
        bookmark.bookmark_type = (
            bookmark_data.bookmark_type.strip()
        )

    if bookmark_data.title is not None:
        bookmark.title = (
            bookmark_data.title.strip()
        )

    if bookmark_data.reference is not None:
        bookmark.reference = (
            bookmark_data.reference.strip()
        )

    db.commit()
    db.refresh(bookmark)

    return bookmark


@router.delete(
    "/{case_id}/bookmarks/{bookmark_id}",
)
def delete_case_bookmark(
    case_id: int,
    bookmark_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    get_owned_case(
        case_id=case_id,
        current_user=current_user,
        db=db,
    )

    bookmark = (
        db.query(CaseBookmark)
        .filter(
            CaseBookmark.id == bookmark_id,
            CaseBookmark.case_id == case_id,
            CaseBookmark.created_by == current_user.id,
        )
        .first()
    )

    if bookmark is None:
        raise HTTPException(
            status_code=404,
            detail="Bookmark not found",
        )

    db.delete(bookmark)
    db.commit()

    return {
        "message": "Bookmark deleted successfully",
        "bookmark_id": bookmark_id,
    }