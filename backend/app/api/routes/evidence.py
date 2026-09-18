from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.case_model import Case
from app.db.evidence_model import CaseEvidence
from app.db.session import get_db
from app.schemas.evidence import (
    CaseEvidenceCreate,
    CaseEvidenceResponse,
    CaseEvidenceUpdate,
)
from app.services.auth import get_current_user


router = APIRouter(
    prefix="/cases",
    tags=["Case Evidence"],
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
    "/{case_id}/evidence",
    response_model=CaseEvidenceResponse,
)
def create_case_evidence(
    case_id: int,
    evidence_data: CaseEvidenceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    get_owned_case(
        case_id=case_id,
        current_user=current_user,
        db=db,
    )

    evidence = CaseEvidence(
        case_id=case_id,
        created_by=current_user.id,
        evidence_type=evidence_data.evidence_type.strip(),
        title=evidence_data.title.strip(),
        description=(
            evidence_data.description.strip()
            if evidence_data.description is not None
            else None
        ),
        reference=(
            evidence_data.reference.strip()
            if evidence_data.reference is not None
            else None
        ),
    )

    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    return evidence


@router.get(
    "/{case_id}/evidence",
    response_model=list[CaseEvidenceResponse],
)
def get_case_evidence(
    case_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    get_owned_case(
        case_id=case_id,
        current_user=current_user,
        db=db,
    )

    evidence_items = (
        db.query(CaseEvidence)
        .filter(
            CaseEvidence.case_id == case_id,
        )
        .order_by(
            CaseEvidence.created_at.asc(),
            CaseEvidence.id.asc(),
        )
        .all()
    )

    return evidence_items


@router.put(
    "/{case_id}/evidence/{evidence_id}",
    response_model=CaseEvidenceResponse,
)
def update_case_evidence(
    case_id: int,
    evidence_id: int,
    evidence_data: CaseEvidenceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    get_owned_case(
        case_id=case_id,
        current_user=current_user,
        db=db,
    )

    evidence = (
        db.query(CaseEvidence)
        .filter(
            CaseEvidence.id == evidence_id,
            CaseEvidence.case_id == case_id,
            CaseEvidence.created_by == current_user.id,
        )
        .first()
    )

    if evidence is None:
        raise HTTPException(
            status_code=404,
            detail="Evidence not found",
        )

    if evidence_data.evidence_type is not None:
        evidence.evidence_type = (
            evidence_data.evidence_type.strip()
        )

    if evidence_data.title is not None:
        evidence.title = evidence_data.title.strip()

    if evidence_data.description is not None:
        evidence.description = (
            evidence_data.description.strip()
        )

    if evidence_data.reference is not None:
        evidence.reference = (
            evidence_data.reference.strip()
        )

    db.commit()
    db.refresh(evidence)

    return evidence


@router.delete(
    "/{case_id}/evidence/{evidence_id}",
)
def delete_case_evidence(
    case_id: int,
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    get_owned_case(
        case_id=case_id,
        current_user=current_user,
        db=db,
    )

    evidence = (
        db.query(CaseEvidence)
        .filter(
            CaseEvidence.id == evidence_id,
            CaseEvidence.case_id == case_id,
            CaseEvidence.created_by == current_user.id,
        )
        .first()
    )

    if evidence is None:
        raise HTTPException(
            status_code=404,
            detail="Evidence not found",
        )

    db.delete(evidence)
    db.commit()

    return {
        "message": "Evidence deleted successfully",
        "evidence_id": evidence_id,
    }