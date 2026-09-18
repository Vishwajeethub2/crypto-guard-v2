from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.case_model import Case
from app.db.session import get_db
from app.db.wallet_model import Wallet

from app.schemas.case import CaseCreate, CaseUpdate
from app.schemas.case_risk import CaseRiskAnalysisResponse
from app.schemas.risk import AdvancedRiskResponse
from app.schemas.graph_analytics import GraphAnalyticsResponse
from app.schemas.timeline import TimelineAnalyticsResponse

from app.services.auth import get_current_user
from app.services.blockchain import validate_wallet_address
from app.services.scoring import calculate_wallet_risk
from app.services.advanced_risk import analyze_wallet_advanced_risk
from app.services.graph_analytics import analyze_wallet_graph_analytics
from app.services.timeline import analyze_wallet_timeline


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


# ============================================================
# WALLET RISK ANALYSIS
# ============================================================

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


# ============================================================
# ADVANCED RISK ANALYSIS
# ============================================================

@router.get(
    "/{case_id}/wallets/{wallet_id}/advanced-risk",
    response_model=AdvancedRiskResponse,
)
def analyze_case_wallet_advanced_risk(
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
        analysis = analyze_wallet_advanced_risk(
            address=wallet.address,
            chain=wallet.chain,
            max_hops=2,
        )

        return analysis

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


# ============================================================
# GRAPH ANALYTICS
# ============================================================

@router.get(
    "/{case_id}/wallets/{wallet_id}/graph-analytics",
    response_model=GraphAnalyticsResponse,
)
def analyze_case_wallet_graph_analytics(
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
        analysis = analyze_wallet_graph_analytics(
            address=wallet.address,
            chain=wallet.chain,
            max_hops=2,
        )

        if analysis is None:
            raise HTTPException(
                status_code=404,
                detail="Wallet graph data not found",
            )

        return analysis

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


# ============================================================
# TIMELINE ANALYTICS
# ============================================================

@router.get(
    "/{case_id}/wallets/{wallet_id}/timeline",
    response_model=TimelineAnalyticsResponse,
)
def analyze_case_wallet_timeline(
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
        analysis = analyze_wallet_timeline(
            address=wallet.address,
            chain=wallet.chain,
        )

        if analysis is None:
            raise HTTPException(
                status_code=404,
                detail="Wallet timeline data not found",
            )

        return analysis

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


# ============================================================
# GET SINGLE CASE
# ============================================================

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


# ============================================================
# UPDATE CASE
# ============================================================

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


# ============================================================
# DELETE CASE
# ============================================================

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