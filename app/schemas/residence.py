from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class ResidenceCreate(BaseModel):
    name: str
    address: Optional[str] = None

class ResidenceOut(BaseModel):
    id: UUID
    name: str
    address: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


