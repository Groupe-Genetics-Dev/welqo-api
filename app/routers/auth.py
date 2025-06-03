
from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.postgres_connect import get_db
from app.models.data import User
from app.schemas.token import Token
from app.oauth2 import create_access_token
from app.utils import verify


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login_for_access_token(user_credentials: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 db: Annotated[Session, Depends(get_db)]):
    user = db.query(User).filter_by(email=user_credentials.username).first()

    if user is None or not verify(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Invalid Credentials")

    access_token = create_access_token(data={
        "user_id": str(user.id), 
        "user_name": user.name
        }
        )

    return {"access_token": access_token, 
            "token_type": "bearer",
            "user_name": user.name
    }
    

