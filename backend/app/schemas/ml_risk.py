from typing import Any

from pydantic import BaseModel, Field


class MLRiskResponse(BaseModel):
    address: str
    chain: str

    prediction: int = Field(
        ge=0,
        le=1,
    )

    probability: float = Field(
        ge=0.0,
        le=1.0,
    )

    model_version: str
    schema_version: str

    features: dict[str, Any]

    status: str = "research_candidate"

    notice: str = (
        "This is a research-stage ML model output. "
        "The probability is not a validated real-world AML "
        "probability and is not a definitive illicit-activity determination."
    )