from fastapi import APIRouter, Depends, HTTPException

from app.api.routes.users import get_current_user
from app.schemas.intelligence import (
    RiskEntityCreate,
    RiskEntityUpdate,
    RiskEntityResponse,
)
from app.services.intelligence import (
    add_risk_entity,
    get_intelligence_risk_entities,
    get_intelligence_risk_entity,
    update_intelligence_risk_entity,
    delete_intelligence_risk_entity,
)

router = APIRouter(
    prefix="/intelligence",
    tags=["Intelligence"],
)


@router.post(
    "/risk-entities",
    response_model=RiskEntityResponse,
)
def create_intelligence_risk_entity(
    payload: RiskEntityCreate,
    current_user=Depends(get_current_user),
):
    try:
        return add_risk_entity(
            address=payload.address,
            chain=payload.chain,
            entity_type=payload.entity_type,
            name=payload.name,
            source=payload.source,
            risk_category=payload.risk_category,
            confidence=payload.confidence,
            evidence=payload.evidence,
            updated_at=payload.updated_at,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.get(
    "/risk-entities",
    response_model=list[RiskEntityResponse],
)
def list_intelligence_risk_entities(
    chain: str | None = None,
    entity_type: str | None = None,
    source: str | None = None,
    risk_category: str | None = None,
    current_user=Depends(get_current_user),
):
    return get_intelligence_risk_entities(
        chain=chain,
        entity_type=entity_type,
        source=source,
        risk_category=risk_category,
    )

@router.get(
    "/risk-entities/{address}",
    response_model=RiskEntityResponse,
)
def get_intelligence_risk_entity_by_address(
    address: str,
    chain: str = "ethereum",
    current_user=Depends(get_current_user),
):
    try:
        return get_intelligence_risk_entity(
            address=address,
            chain=chain,
        )
    except ValueError as error:
        if str(error) == "Risk entity not found":
            raise HTTPException(
                status_code=404,
                detail=str(error),
            )

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

@router.put(
    "/risk-entities/{address}",
    response_model=RiskEntityResponse,
)
def update_intelligence_risk_entity_by_address(
    address: str,
    payload: RiskEntityUpdate,
    chain: str = "ethereum",
    current_user=Depends(get_current_user),
):
    try:
        return update_intelligence_risk_entity(
            address=address,
            chain=chain,
            entity_type=payload.entity_type,
            name=payload.name,
            source=payload.source,
            risk_category=payload.risk_category,
            confidence=payload.confidence,
            evidence=payload.evidence,
            updated_at=payload.updated_at,
        )

    except ValueError as error:
        if str(error) == "Risk entity not found":
            raise HTTPException(
                status_code=404,
                detail=str(error),
            )

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

@router.delete(
    "/risk-entities/{address}",
)
def delete_intelligence_risk_entity_by_address(
    address: str,
    chain: str = "ethereum",
    current_user=Depends(get_current_user),
):
    try:
        return delete_intelligence_risk_entity(
            address=address,
            chain=chain,
        )

    except ValueError as error:
        if str(error) == "Risk entity not found":
            raise HTTPException(
                status_code=404,
                detail=str(error),
            )

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )