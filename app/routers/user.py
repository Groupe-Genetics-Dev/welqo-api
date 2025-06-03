from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.schemas.user import UserCreate, UserOut, ChangePassword, ForgotPassword
from app.models.data import User
from app.postgres_connect import get_db
from app.utils import hashed, verify


router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]):
    # Vérifier si l'email existe déjà
    if db.query(User).filter_by(email=user.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Utilisateur avec email ({user.email}) existe déjà"
        )

    # Créer l'utilisateur
    new_user = User(
        name=user.name,
        email=user.email,
        password=hashed(user.password),
        phone_number=user.phone_number
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@router.put("/change-password", status_code=status.HTTP_200_OK)
async def change_password(data: ChangePassword, db: Annotated[Session, Depends(get_db)]):
    user = db.query(User).filter_by(email=data.email).first()
    if not user or not verify(data.old_password, user.password):
        raise HTTPException(status_code=403, detail="Ancien mot de passe incorrect.")

    user.password = hashed(data.new_password)
    db.commit()
    return {"message": "Mot de passe mis à jour avec succès."}

@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(data: ForgotPassword, db: Annotated[Session, Depends(get_db)]):
    user = db.query(User).filter_by(email=data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email non trouvé.")

    user.password = hashed(data.new_password)
    db.commit()
    return {"message": "Mot de passe réinitialisé avec succès."}

@router.get("/all", response_model=list[UserOut])
async def get_all_users(db: Annotated[Session, Depends(get_db)]):
    users = db.query(User).all()
    return users


