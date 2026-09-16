from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.case_model import Case
from app.db.session import get_db
from app.db.wallet_model import Wallet
from app.schemas.case import CaseCreate, CaseUpdate
from app.schemas.case_risk import CaseRiskAnalysisResponse
from app.services.auth import get_current_user
from app.services.blockchain import validate_wallet_address
from app.services.scoring import calculate_wallet_risk


router = APIRouter(
    prefix="/cases",
    tags=["Cases"],
)


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


@router.get("/")
def get_cases(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    cases = (
        db.query(Case)
        .filter(Case.created_by == current_user.id)
        .all()
    )

    return [
        {
            "id": case.id,
            "title": case.title,
            "description": case.description,
            "status": case.status,
            "created_by": case.created_by,
            "created_at": case.created_at,
        }
        for case in cases
    ]


@router.get(
    "/{case_id}/wallets/{wallet_id}/risk",
    response_model=CaseRiskAnalysisResponse,
)
def analyze_case_wallet_risk(
    case_id: int,
    wallet_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
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

    wallet = (
        db.query(Wallet)
        .filter(
            Wallet.id == wallet_id,
            Wallet.case_id == case_id,
        )
        .first()
    )

    if wallet is None:
        raise HTTPException(
            status_code=404,
            detail="Wallet not found in this case",
        )

    if not validate_wallet_address(wallet.address):
        raise HTTPException(
            status_code=400,
            detail="Invalid wallet address",
        )

    try:
        analysis = calculate_wallet_risk(
            address=wallet.address,
            chain=wallet.chain,
            max_hops=2,
        )

        return {
            "case_id": case.id,
            "wallet_id": wallet.id,
            "wallet_address": wallet.address,
            "wallet_chain": wallet.chain,
            "wallet_label": wallet.label,
            "analysis": analysis,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.get("/{case_id}")
def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
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

    return {
        "id": case.id,
        "title": case.title,
        "description": case.description,
        "status": case.status,
        "created_by": case.created_by,
        "created_at": case.created_at,
    }


@router.put("/{case_id}")
def update_case(
    case_id: int,
    case_data: CaseUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
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

    if case_data.title is not None:
        case.title = case_data.title

    if case_data.description is not None:
        case.description = case_data.description

    if case_data.status is not None:
        case.status = case_data.status

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


@router.delete("/{case_id}")
def delete_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
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

    db.delete(case)
    db.commit()

    return {
        "message": "Case deleted successfully",
        "case_id": case_id,
    }