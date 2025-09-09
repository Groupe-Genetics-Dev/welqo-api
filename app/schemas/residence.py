# app/schemas/residence.py
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.schemas.owner import OwnerOut

class ResidenceCreate(BaseModel):
    name: str
    address: Optional[str] = None

class ResidenceOut(BaseModel):
    id: UUID
    name: str
    address: Optional[str]
    created_at: Optional[datetime]
    owners: List[OwnerOut] = []   # ✅ ajouter les infos du propriétaire/gestionnaire

    class Config:
        from_attributes = True
