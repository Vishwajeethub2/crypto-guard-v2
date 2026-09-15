from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.case_model import Case
from app.db.wallet_model import Wallet
from app.db.session import get_db
from app.schemas.wallet import WalletCreate
from app.services.auth import get_current_user
from app.services.blockchain import validate_wallet_address


router = APIRouter(prefix="/wallets", tags=["Wallets"])


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


@router.get("/{wallet_id}")
def get_wallet(
    wallet_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    wallet = (
        db.query(Wallet)
        .join(Case, Wallet.case_id == Case.id)
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
        .join(Case, Wallet.case_id == Case.id)
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