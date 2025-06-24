from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.schemas.owner import ForgotPasswordRequest, MessageResponse, ResetPasswordRequest
from app.schemas.user import UserCreate, UserOut, ChangePassword
from app.models.data import User
from app.postgres_connect import get_db
from app.utils import hashed, verify
from app.oauth2 import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]):
    try:
        if db.query(User).filter_by(phone_number=user.phone_number).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"L'utilisateur avec ce numéro de téléphone existe déjà."
            )

        new_user = User(
            name=user.name,
            password=hashed(user.password),
            phone_number=user.phone_number,
            appartement=user.appartement
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur de base de données: {str(e)}"
        )

@router.get("/users/me", response_model=UserOut)
async def get_current_user(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/change-password", status_code=status.HTTP_200_OK)
async def change_password(data: ChangePassword, db: Annotated[Session, Depends(get_db)]):
    user = db.query(User).filter_by(phone_number=data.phone_number).first()
    if not user or not verify(data.old_password, user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ancien mot de passe incorrect."
        )

    user.password = hashed(data.new_password)
    db.commit()
    return {"message": "Mot de passe mis à jour avec succès."}


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    # Vérifiez si le numéro de téléphone existe dans la base de données
    owner = db.query(User).filter(User.phone_number == request.phone_number).first()
    if not owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Numéro de téléphone non trouvé")

    return {"message": "Numéro de téléphone valide. Veuillez saisir votre nouveau mot de passe."}

@router.post("/reset-password", response_model=MessageResponse)
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    # Vérifiez si le numéro de téléphone existe dans la base de données
    owner = db.query(User).filter(User.phone_number == request.phone_number).first()
    if not owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Numéro de téléphone non trouvé")

    # Vérifiez si les mots de passe correspondent
    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Les mots de passe ne correspondent pas")

    # Réinitialiser le mot de passe
    owner.password = hashed(request.new_password)
    db.commit()
    db.refresh(owner)

    return {"message": "Mot de passe réinitialisé avec succès"}



@router.get("/all", response_model=list[UserOut])
async def get_all_users(db: Annotated[Session, Depends(get_db)]):
    users = db.query(User).all()
    return users

