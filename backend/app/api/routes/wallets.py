from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.case_model import Case
from app.db.neo4j import get_transaction_details, trace_wallet
from app.db.session import get_db
from app.db.wallet_model import Wallet
from app.schemas.risk import WalletRiskAnalysisResponse
from app.schemas.wallet import WalletCreate
from app.services.auth import get_current_user
from app.services.ingestion import (
    ingest_live_transfers_bidirectional,
    ingest_live_transfers_recursive,
)
from app.services.blockchain import validate_wallet_address
from app.services.scoring import calculate_wallet_risk
from app.services.peel_chain_analysis import analyze_peel_chain
from app.services.cross_chain_analysis import analyze_cross_chain
from app.services.candidate_linking import analyze_candidate_linking


router = APIRouter(
    prefix="/wallets",
    tags=["Wallets"],
)


@router.post("/")
def create_wallet(
    wallet_data: WalletCreate,
    case_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not validate_wallet_address(wallet_data.address):
        raise HTTPException(
            status_code=400,
            detail="Invalid wallet address",
        )

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

    wallet = Wallet(
        case_id=case_id,
        address=wallet_data.address,
        chain=wallet_data.chain,
        label=wallet_data.label,
    )

    db.add(wallet)
    db.commit()
    db.refresh(wallet)

    return {
        "id": wallet.id,
        "case_id": wallet.case_id,
        "address": wallet.address,
        "chain": wallet.chain,
        "label": wallet.label,
        "created_at": wallet.created_at,
    }


@router.get("/")
def get_wallets(
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

    wallets = (
        db.query(Wallet)
        .filter(Wallet.case_id == case_id)
        .all()
    )

    return [
        {
            "id": wallet.id,
            "case_id": wallet.case_id,
            "address": wallet.address,
            "chain": wallet.chain,
            "label": wallet.label,
            "created_at": wallet.created_at,
        }
        for wallet in wallets
    ]


@router.get(
    "/risk/{address}",
    response_model=WalletRiskAnalysisResponse,
)
def analyze_wallet_risk_api(
    address: str,
    chain: str = "ethereum",
    max_hops: int = 2,
    current_user=Depends(get_current_user),
):
    if not validate_wallet_address(address):
        raise HTTPException(
            status_code=400,
            detail="Invalid wallet address",
        )

    try:
        result = calculate_wallet_risk(
            address=address,
            chain=chain,
            max_hops=max_hops,
        )

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.get("/trace/{address}")
def trace_wallet_api(
    address: str,
    chain: str = "ethereum",
    direction: str = "both",
    max_hops: int = 2,
    refresh_live: bool = True,
    max_live_wallets: int = 25,
    max_live_transfers_per_wallet: int = 10,
    current_user=Depends(get_current_user),
):
    if not validate_wallet_address(address):
        raise HTTPException(
            status_code=400,
            detail="Invalid wallet address",
        )

    try:
        live_refresh_result = None

        if refresh_live:
            live_refresh_result = ingest_live_transfers_recursive(
                chain=chain,
                address=address,
                max_hops=max_hops,
                max_wallets=max_live_wallets,
                max_transfers_per_wallet=max_live_transfers_per_wallet,
            )

        traces = trace_wallet(
            address=address,
            chain=chain,
            direction=direction,
            max_hops=max_hops,
        )

        return {
            "address": address,
            "chain": chain.lower(),
            "direction": direction.lower(),
            "max_hops": max_hops,
            "refresh_live": refresh_live,
            "max_live_wallets": max_live_wallets,
            "max_live_transfers_per_wallet": max_live_transfers_per_wallet,
            "live_refresh": live_refresh_result,
            "trace_count": len(traces),
            "traces": traces,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.get("/peel-chain/{address}")
def analyze_peel_chain_api(
    address: str,
    chain: str = "ethereum",
    max_hops: int = 5,
    current_user=Depends(get_current_user),
):
    """
    Analyze existing Neo4j transaction data for peel-chain candidates.

    This endpoint does NOT perform live blockchain/API ingestion.
    It only analyzes transaction data already stored in Neo4j.
    """

    if not validate_wallet_address(address):
        raise HTTPException(
            status_code=400,
            detail="Invalid wallet address",
        )

    try:
        result = analyze_peel_chain(
            address=address,
            chain=chain,
            max_hops=max_hops,
        )

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.get("/cross-chain/{address}")
def analyze_cross_chain_api(
    address: str,
    source_chain: str = "ethereum",
    target_chain: str | None = None,
    time_window_minutes: int = 120,
    value_tolerance: float = 0.20,
    current_user=Depends(get_current_user),
):
    """
    Analyze existing Neo4j transaction data for possible cross-chain links.

    This endpoint does NOT perform live blockchain/API ingestion.
    It only analyzes transaction data already stored in Neo4j.

    Cross-chain links are research candidates based on matching signals,
    not confirmed bridge attribution.
    """

    if not validate_wallet_address(address):
        raise HTTPException(
            status_code=400,
            detail="Invalid wallet address",
        )

    if time_window_minutes < 1 or time_window_minutes > 1440:
        raise HTTPException(
            status_code=400,
            detail="time_window_minutes must be between 1 and 1440",
        )

    if value_tolerance < 0 or value_tolerance > 1:
        raise HTTPException(
            status_code=400,
            detail="value_tolerance must be between 0 and 1",
        )

    try:
        return analyze_cross_chain(
            address=address,
            source_chain=source_chain,
            target_chain=target_chain,
            time_window_minutes=time_window_minutes,
            value_tolerance=value_tolerance,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.get("/candidate-linking/{address}")
def analyze_candidate_linking_api(
    address: str,
    chain: str = "ethereum",
    max_hops: int = 2,
    current_user=Depends(get_current_user),
):
    """
    Analyze existing VASP intelligence and transaction-path
    evidence for candidate wallet-to-VASP links.

    This endpoint does not perform live blockchain/API ingestion.
    It uses existing intelligence and Neo4j transaction evidence.
    """

    if not validate_wallet_address(address):
        raise HTTPException(
            status_code=400,
            detail="Invalid wallet address",
        )

    try:
        return analyze_candidate_linking(
            address=address,
            chain=chain,
            max_hops=max_hops,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.get("/transaction/{transaction_hash}")
def get_transaction_details_api(
    transaction_hash: str,
    current_user=Depends(get_current_user),
):
    transaction = get_transaction_details(
        transaction_hash=transaction_hash,
    )

    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )

    return transaction


@router.get("/{wallet_id}")
def get_wallet(
    wallet_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    wallet = (
        db.query(Wallet)
        .join(
            Case,
            Wallet.case_id == Case.id,
        )
        .filter(
            Wallet.id == wallet_id,
            Case.created_by == current_user.id,
        )
        .first()
    )

    if wallet is None:
        raise HTTPException(
            status_code=404,
            detail="Wallet not found",
        )

    return {
        "id": wallet.id,
        "case_id": wallet.case_id,
        "address": wallet.address,
        "chain": wallet.chain,
        "label": wallet.label,
        "created_at": wallet.created_at,
    }


@router.delete("/{wallet_id}")
def delete_wallet(
    wallet_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    wallet = (
        db.query(Wallet)
        .join(
            Case,
            Wallet.case_id == Case.id,
        )
        .filter(
            Wallet.id == wallet_id,
            Case.created_by == current_user.id,
        )
        .first()
    )

    if wallet is None:
        raise HTTPException(
            status_code=404,
            detail="Wallet not found",
        )

    db.delete(wallet)
    db.commit()

    return {
        "message": "Wallet deleted successfully",
        "wallet_id": wallet_id,
    }