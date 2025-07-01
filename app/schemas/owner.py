from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional

class OwnerCreate(BaseModel):
    name: str
    phone_number: str
    email: EmailStr
    password: str

class OwnerOut(BaseModel):
    id: UUID
    name: str
    phone_number: str
    logo_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


 
class ForgotPasswordRequest(BaseModel):
    phone_number: str

class ResetPasswordRequest(BaseModel):
    phone_number: str
    new_password: str
    confirm_password: str

class MessageResponse(BaseModel):
    message: str

    
