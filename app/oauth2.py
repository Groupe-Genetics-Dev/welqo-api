from fastapi import  Depends, HTTPException, status
from datetime import datetime, timedelta
from jose import jwt, JWTError
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer
from requests import Session

from app.config import settings
from app.models.data import Guard, User
from app.schemas.token import  TokenData
from app.postgres_connect import get_db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        user_name: str = payload.get("user_name")
        guard_id: str = payload.get("guard_id")
        guard_name: str = payload.get("guard_name")

        if user_id is None and guard_id is None:
            raise credentials_exception

        token_data = TokenData(id=user_id, user_name=user_name, guard_id=guard_id, guard_name=guard_name)

    except JWTError:
        raise credentials_exception

    return token_data


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = verify_access_token(token, credentials_exception)

    if token_data.id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == token_data.id).first()

    if user is None:
        raise credentials_exception

    return user

def get_current_guard(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = verify_access_token(token, credentials_exception)

    if token_data.guard_id is None:
        raise credentials_exception

    guard = db.query(Guard).filter(Guard.id == token_data.guard_id).first()

    if guard is None:
        raise credentials_exception

    return guard


