from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.case_model import Case
from app.db.neo4j import get_transaction_details, trace_wallet
from app.db.session import get_db
from app.db.wallet_model import Wallet
from app.schemas.risk import WalletRiskAnalysisResponse
from app.schemas.wallet import WalletCreate
from app.services.auth import get_current_user
from app.services.blockchain import validate_wallet_address
from app.services.scoring import calculate_wallet_risk


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
    current_user=Depends(get_current_user),
):
    if not validate_wallet_address(address):
        raise HTTPException(
            status_code=400,
            detail="Invalid wallet address",
        )

    try:
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
            "trace_count": len(traces),
            "traces": traces,
        }

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