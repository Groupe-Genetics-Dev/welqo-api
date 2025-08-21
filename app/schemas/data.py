import uuid
import re
from datetime import datetime
from pydantic import BaseModel, field_validator
from typing import Optional

from app.schemas.user import UserOut

class FormDataCreate(BaseModel):
    name: str
    phone_number: str
    duration_minutes: int
    apartment_number: Optional[str] = None  # <-- AJOUT ICI

    @field_validator('phone_number')
    def validate_phone(cls, value: str) -> str:
        patterns = {
            'SN': r'^\+221\d{9}$'
        }

        for pattern in patterns.values():
            if re.match(pattern, value):
                return value

        raise ValueError("Numéro de téléphone invalide. Veuillez inclure l'indicatif du pays.")


class FormDataResponse(BaseModel):
    id: uuid.UUID
    name: str
    phone_number: str
    apartment_number: Optional[str]  # <-- AJOUT ICI
    qr_code_data: Optional[str]
    created_at: datetime
    expires_at: datetime
    user: UserOut

    class Config:
        from_attributes = True


class UserInfo(BaseModel):
    name: str
    phone_number: str
    appartement: str


class VisitorInfo(BaseModel):
    name: str
    phone_number: str


class QRValidationData(BaseModel):
    user: UserInfo
    visitor: VisitorInfo
    created_at: datetime
    expires_at: datetime


class QRValidationResponse(BaseModel):
    valid: bool
    message: str
    data: Optional[QRValidationData] = None


class FormDataUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None  
    duration_minutes: Optional[int] = None
    apartment_number: Optional[str] = None  # <-- AJOUT ICI

    @field_validator('phone_number')  
    def validate_phone_update(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value

        patterns = {
            'SN': r'^\+221\d{9}$'
        }

        for pattern in patterns.values():
            if re.match(pattern, value):
                return value

        raise ValueError("Numéro de téléphone invalide. Veuillez inclure l'indicatif du pays.")

