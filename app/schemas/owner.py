from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class OwnerCreate(BaseModel):
    name: str
    phone_number: str
    password: str

class OwnerOut(BaseModel):
    id: UUID
    name: str
    phone_number: str
    logo_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True




