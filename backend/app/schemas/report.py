from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CaseReportResponse(BaseModel):
    id: int
    case_id: int
    created_by: int
    report_type: str
    file_name: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)