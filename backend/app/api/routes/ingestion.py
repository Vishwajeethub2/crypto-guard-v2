from fastapi import APIRouter, Depends

from app.services.ingestion import (
    ingest_saved_transfers,
    ingest_live_transfers,
)
from app.api.routes.users import get_current_user


router = APIRouter(
    prefix="/ingestion",
    tags=["Ingestion"],
)


@router.post("/saved")
def ingest_saved_blockchain_data(
    chain: str = "ethereum",
    current_user=Depends(get_current_user),
):
    return ingest_saved_transfers(chain=chain)

@router.post("/live")
def ingest_live_blockchain_data(
    address: str,
    chain: str = "ethereum",
    max_count: int = 20,
    current_user=Depends(get_current_user),
):
    try:
        return ingest_live_transfers(
            chain=chain,
            address=address,
            max_count=max_count,
        )
    except ValueError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )