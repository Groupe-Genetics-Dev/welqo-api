from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional

class GuardBase(BaseModel):
    name: str
    phone_number: str

class GuardCreate(GuardBase):
    password: str

    class Config:
        from_attributes = True
        orm_mode = True

class GuardOut(GuardBase):
    id: UUID
    created_at: datetime

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


