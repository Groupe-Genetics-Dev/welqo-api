
from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class Token(BaseModel):
    access_token: str
    token_type: str
    user_name: str
    residence_id: UUID


class TokenData(BaseModel):
    id: Optional[UUID] = None
    user_name: Optional[str] = None
    guard_id: Optional[UUID] = None
    guard_name: Optional[str] = None
    residence_id: Optional[UUID] = None


    

    

