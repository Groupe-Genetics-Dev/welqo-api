from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone_number: str 

class UserOut(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    phone_number: str 
    created_at: datetime

class ChangePassword(BaseModel):
    email: EmailStr
    old_password: str
    new_password: str


class ForgotPassword(BaseModel):
    email: EmailStr
    new_password: str

    class Config:
       from_attributes = True



