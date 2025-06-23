from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class QRScanRequest(BaseModel):
    form_id: UUID

class UserInfo(BaseModel):
    name: str
    phone_number: str
    appartement: str

class VisitorInfo(BaseModel):
    name: str
    phone_number: str

class QRScanData(BaseModel):
    user: UserInfo
    visitor: VisitorInfo
    created_at: datetime
    expires_at: datetime
    form_id: UUID

class QRScanResponse(BaseModel):
    valid: bool
    message: str
    data: Optional[QRScanData] = None

class QRConfirmRequest(BaseModel):
    form_id: UUID
    confirmed: bool

class QRConfirmResponse(BaseModel):
    success: bool
    message: str
    scan_id: Optional[UUID] = None

class GuardQRScanOut(BaseModel):
    id: UUID
    form_id: UUID
    guard_id: UUID
    confirmed: Optional[bool] = None
    scanned_at: datetime
    created_at: datetime
    updated_at: datetime
    visitor_name: Optional[str] = None
    visitor_phone: Optional[str] = None
    resident_name: Optional[str] = None
    resident_phone: Optional[str] = None
    resident_apartment: Optional[str] = None
    expires_at: Optional[datetime] = None
    valid: Optional[bool] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_details(cls, scan_obj):
        data = {
            "id": scan_obj.id,
            "form_id": scan_obj.form_data_id,
            "guard_id": scan_obj.guard_id,
            "confirmed": scan_obj.confirmed,
            "scanned_at": scan_obj.scanned_at,
            "created_at": scan_obj.created_at,
            "updated_at": scan_obj.updated_at,
        }

        if scan_obj.form_data:
            data.update({
                "visitor_name": scan_obj.form_data.name,
                "visitor_phone": scan_obj.form_data.phone_number,
                "expires_at": scan_obj.form_data.expires_at,
                "valid": datetime.now() <= scan_obj.form_data.expires_at,
            })

            if scan_obj.form_data.user:
                data.update({
                    "resident_name": scan_obj.form_data.user.name,
                    "resident_phone": scan_obj.form_data.user.phone_number,
                    "resident_apartment": scan_obj.form_data.user.appartement,
                })

        return cls(**data)

