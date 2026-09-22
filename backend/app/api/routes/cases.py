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
from app.schemas.ml_risk import MLRiskResponse

from app.services.auth import get_current_user
from app.services.blockchain import validate_wallet_address
from app.services.scoring import calculate_wallet_risk
from app.services.advanced_risk import analyze_wallet_advanced_risk
from app.services.graph_analytics import analyze_wallet_graph_analytics
from app.services.timeline import analyze_wallet_timeline
from app.services.vasp_attribution import analyze_vasp_attribution

from app.services.ml_features import build_ml_features
from app.services.ml_model import get_ml_model
from app.services.aml_determination import (
    build_aml_evidence_assessment,
)


router = APIRouter(
    prefix="/cases",
    tags=["Cases"],
)


# ============================================================
# CREATE CASE
# ============================================================

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


# ============================================================
# GET ALL CASES
# ============================================================

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
# ============================================================
# VASP ATTRIBUTION
# ============================================================

@router.get(
    "/{case_id}/wallets/{wallet_id}/vasp-attribution",
)
def analyze_case_wallet_vasp_attribution(
    case_id: int,
    wallet_id: int,
    max_hops: int = 2,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Identify known VASP intelligence entities connected to a wallet.

    This endpoint uses existing Neo4j transfer relationships and
    known VASP intelligence records. It does not make a new
    blockchain/Alchemy request.
    """

    # ----------------------------------------------------------
    # Verify case ownership
    # ----------------------------------------------------------

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

    # ----------------------------------------------------------
    # Verify wallet belongs to case
    # ----------------------------------------------------------

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

    # ----------------------------------------------------------
    # Validate address
    # ----------------------------------------------------------

    if not validate_wallet_address(wallet.address):
        raise HTTPException(
            status_code=400,
            detail="Invalid wallet address",
        )

    # ----------------------------------------------------------
    # Validate hop range
    # ----------------------------------------------------------

    if max_hops < 0 or max_hops > 2:
        raise HTTPException(
            status_code=400,
            detail="max_hops must be between 0 and 2",
        )

    try:
        analysis = analyze_vasp_attribution(
            address=wallet.address,
            chain=wallet.chain,
            max_hops=max_hops,
        )

        return {
            "case_id": case.id,
            "wallet_id": wallet.id,
            "wallet_address": wallet.address,
            "wallet_chain": wallet.chain,
            **analysis,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

# ML RISK ANALYSIS
# ============================================================

@router.get(
    "/{case_id}/wallets/{wallet_id}/ml-risk",
    response_model=MLRiskResponse,
)
def analyze_case_wallet_ml_risk(
    case_id: int,
    wallet_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Generate the research-stage ML prediction for a wallet.

    This endpoint uses Crypto Guard's existing graph and timeline
    analytics to construct the ML feature vector.

    It does not make a new Alchemy request.
    """

    # ----------------------------------------------------------
    # Verify case ownership
    # ----------------------------------------------------------

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

    # ----------------------------------------------------------
    # Verify wallet belongs to case
    # ----------------------------------------------------------

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

    # ----------------------------------------------------------
    # Validate address
    # ----------------------------------------------------------

    if not validate_wallet_address(wallet.address):
        raise HTTPException(
            status_code=400,
            detail="Invalid wallet address",
        )

    try:
        # ------------------------------------------------------
        # Existing Crypto Guard graph analysis
        # ------------------------------------------------------

        graph = analyze_wallet_graph_analytics(
            address=wallet.address,
            chain=wallet.chain,
            max_hops=2,
        )

        if graph is None:
            raise HTTPException(
                status_code=404,
                detail="Wallet graph data not found",
            )

        # ------------------------------------------------------
        # Existing Crypto Guard timeline analysis
        # ------------------------------------------------------

        timeline = analyze_wallet_timeline(
            address=wallet.address,
            chain=wallet.chain,
        )

        if timeline is None:
            raise HTTPException(
                status_code=404,
                detail="Wallet timeline data not found",
            )

        # ------------------------------------------------------
        # Build standardized ML feature vector
        #
        # The graph analytics response already contains:
        # - transaction counts
        # - incoming/outgoing values
        # - counterparties
        # - fan-in/fan-out
        # - concentration
        # - multi-hop exposure
        #
        # Therefore we can use graph as the behavioral source
        # for the first integrated implementation.
        # ------------------------------------------------------

        features = build_ml_features(
            behavior=graph,
            graph=graph,
            timeline=timeline,
        )

        # ------------------------------------------------------
        # Load cached ML model
        # ------------------------------------------------------

        model = get_ml_model()

        # ------------------------------------------------------
        # Generate prediction
        # ------------------------------------------------------

        result = model.predict(
            features
        )

        return {
            "address": wallet.address,
            "chain": wallet.chain,
            "prediction": result["prediction"],
            "probability": result["probability"],
            "model_version": result["model_version"],
            "schema_version": result["schema_version"],
            "features": result["feature_values"],
            "status": "research_candidate",
            "notice": (
                "This is a research-stage ML model output. "
                "The probability is not a validated real-world "
                "AML probability and is not a definitive "
                "illicit-activity determination."
            ),
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=503,
            detail=f"ML model unavailable: {error}",
        )


# ============================================================
# AML EVIDENCE ASSESSMENT
# ============================================================

@router.get(
    "/{case_id}/wallets/{wallet_id}/aml-assessment",
)
def analyze_case_wallet_aml_assessment(
    case_id: int,
    wallet_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Build a research-stage AML evidence assessment.

    This endpoint combines existing graph analytics,
    timeline analytics, and the research-stage ML output.

    It does not make a new Alchemy request.
    It does not produce a definitive illicit-activity
    determination.
    """

    case = (
        db.query(Case)
        .filter(
            Case.id == case_id,
            Case.created_by == current_user.id,
        )
        .first()
    )

    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")

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
        graph = analyze_wallet_graph_analytics(
            address=wallet.address,
            chain=wallet.chain,
            max_hops=2,
        )

        if graph is None:
            raise HTTPException(
                status_code=404,
                detail="Wallet graph data not found",
            )

        timeline = analyze_wallet_timeline(
            address=wallet.address,
            chain=wallet.chain,
        )

        if timeline is None:
            raise HTTPException(
                status_code=404,
                detail="Wallet timeline data not found",
            )

        features = build_ml_features(
            behavior=graph,
            graph=graph,
            timeline=timeline,
        )

        model = get_ml_model()
        ml_result = model.predict(features)

        assessment = build_aml_evidence_assessment(
            graph=graph,
            timeline=timeline,
            ml_result=ml_result,
        )

        return {
            "address": wallet.address,
            "chain": wallet.chain,
            **assessment,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=503,
            detail=f"ML model unavailable: {error}",
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

