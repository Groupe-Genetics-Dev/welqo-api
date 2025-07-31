from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import UUID
from typing import Optional
from typing import List


class GuardBase(BaseModel):
    name: str
    email: EmailStr | None = None
    phone_number: str

class GuardCreate(GuardBase):
    password: str
    residence_name: str

    class Config:
        from_attributes = True

class GuardOut(GuardBase):
    id: UUID
    created_at: datetime
    residence_id: UUID 

    class Config:
        from_attributes = True

class GuardQRScanOut(BaseModel):
    id: UUID
    scan_time: datetime
    qr_code_data: str
    guard_id: UUID
    

class GuardUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None


class AttendanceOut(BaseModel):
    id: UUID
    start_time: datetime
    end_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class GuardAttendanceOut(BaseModel):
    guard_id: UUID
    guard_name: str
    attendances: List[AttendanceOut]
    
