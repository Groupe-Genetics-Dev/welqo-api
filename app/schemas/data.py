import uuid
import re
from datetime import datetime
from pydantic import BaseModel, field_validator
from typing import Optional

from app.schemas.user import UserOut

class FormDataCreate(BaseModel):
    name: str
    phone: str
    duration_minutes: int

    @field_validator('phone')
    def validate_phone(cls, value: str) -> str:
        patterns = {
            'SN': r'^\+221\d{9}$'
        }

        for pattern in patterns.values():
            if re.match(pattern, value):
                return value

        raise ValueError('Numéro de téléphone invalide. Veuillez inclure l\'indicatif du pays.')

class FormDataResponse(BaseModel):
    id: uuid.UUID
    name: str
    phone: str
    qr_code_data: Optional[str]
    created_at: datetime
    expires_at: datetime
    user: UserOut

    class Config:
        from_attributes = True

class QRValidationData(BaseModel):
    name: str
    phone: str
    created_at: datetime
    expires_at: datetime

class QRValidationResponse(BaseModel):
    valid: bool
    message: str
    data: Optional[QRValidationData] = None

class FormDataUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    duration_minutes: Optional[int] = None

    @field_validator('phone')
    def validate_phone_update(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value

        patterns = {
            'SN': r'^\+221\d{9}$'
        }

        for pattern in patterns.values():
            if re.match(pattern, value):
                return value

        raise ValueError('Numéro de téléphone invalide. Veuillez inclure l\'indicatif du pays.')

