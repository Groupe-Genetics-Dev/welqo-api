from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class QRScanRequest(BaseModel):
    qr_code_data: str

class QRScanResponse(BaseModel):
    valid: bool
    message: str
    user_info: Optional[dict] = None
    visitor_info: Optional[dict] = None
    duration_minutes: Optional[int] = None

class GuardQRScanOut(BaseModel):
    id: UUID
    scan_time: datetime
    qr_code_data: str
    guard_id: UUID
    form_data_id: UUID

    class Config:
        from_attributes = True

