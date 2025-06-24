from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

from enum import Enum

class ReportType(str, Enum):
    USER_REPORT = "user_report"
    QR_CODE_REPORT = "qr_code_report"
    ACTIVITY_REPORT = "activity_report"
    SECURITY_REPORT = "security_report"



class ReportCreate(BaseModel):
    title: str
    owner_id: UUID
    report_type: ReportType
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

class ReportOut(BaseModel):
    id: UUID
    title: str
    file_path: str
    report_type: ReportType
    created_at: datetime

    class Config:
        from_attributes = True


class StatisticsOut(BaseModel):
    total_users: int
    total_qr_codes: int
    active_qr_codes: int
    total_scans: int
    users_this_month: int
    qr_codes_this_month: int

   
   