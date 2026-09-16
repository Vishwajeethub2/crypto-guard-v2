from pydantic import BaseModel

from app.schemas.risk import WalletRiskAnalysisResponse


class CaseRiskAnalysisResponse(BaseModel):
    case_id: int
    wallet_id: int

    wallet_address: str
    wallet_chain: str
    wallet_label: str | None = None

    analysis: WalletRiskAnalysisResponse