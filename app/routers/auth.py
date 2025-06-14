from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import  datetime, timedelta
from typing import Annotated

from app.config import settings
from app.oauth2 import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, get_current_guard
from app.postgres_connect import get_db
from app.models.data import Attendance, Owner, User, Guard
from app.schemas.token import Token
from app.utils import verify

router = APIRouter(tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/user/login", response_model=Token)
async def login_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.phone_number == form_data.username).first()
    if not user or not verify(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user_id": str(user.id), "user_name": user.name}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "user_name": user.name
    }


@router.post("/guard/login", response_model=Token)
async def login_guard(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    guard = db.query(Guard).filter(Guard.phone_number == form_data.username).first()
    if not guard or not verify(form_data.password, guard.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Enregistrez l'heure de début de session
    attendance = Attendance(
        start_time=datetime.now(),
        guard_id=guard.id
    )
    db.add(attendance)
    db.commit()

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"guard_id": str(guard.id), "guard_name": guard.name},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_name": guard.name
    }

@router.post("/guard/logout")
async def logout_guard(
    current_guard: Guard = Depends(get_current_guard),
    db: Session = Depends(get_db)
):
    attendance = db.query(Attendance).filter(
        Attendance.guard_id == current_guard.id,
        Attendance.end_time == None
    ).order_by(Attendance.start_time.desc()).first()

    if attendance:
        attendance.end_time = datetime.utcnow()
        db.commit()

    return {"message": "Déconnexion réussie"}


@router.post("/owner/login", response_model=Token)
async def login_owner(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    owner = db.query(Owner).filter(Owner.phone_number == form_data.username).first()
    if not owner or not verify(form_data.password, owner.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"owner_id": str(owner.id), "owner_name": owner.name},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_name": owner.name
    }


