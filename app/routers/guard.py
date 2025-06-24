from typing import Annotated, List
from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.oauth2 import get_current_guard
from app.schemas.guard import GuardCreate, GuardOut, GuardQRScanOut, GuardUpdate
from app.models.data import Guard, GuardQRScan
from app.postgres_connect import get_db
from app.schemas.owner import ForgotPasswordRequest, MessageResponse, ResetPasswordRequest
from app.utils import hashed


router = APIRouter(prefix="/guards", tags=["Guards"])

@router.post("/create-guard", response_model=GuardOut, status_code=status.HTTP_201_CREATED)
async def create_guard(guard: GuardCreate, db: Session = Depends(get_db)):
    # Vérifiez si un gardien avec le même numéro de téléphone existe déjà
    existing_guard = db.query(Guard).filter(Guard.phone_number == guard.phone_number).first()
    if existing_guard:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un gardien avec ce numéro de téléphone existe déjà."
        )

    # Hachez le mot de passe avant de le stocker
    hashed_password = hashed(guard.password)

    # Créez un nouveau gardien
    new_guard = Guard(
        name=guard.name,
        password=hashed_password,
        phone_number=guard.phone_number
    )

    # Ajoutez le nouveau gardien à la base de données
    db.add(new_guard)
    db.commit()
    db.refresh(new_guard)

    return new_guard


@router.get("/all", response_model=List[GuardOut])
async def get_all_guards(db: Session = Depends(get_db)):
    guards = db.query(Guard).all()
    return guards


# CORRIGÉ : Déplacé l'endpoint /profile AVANT l'endpoint /{guard_id}
@router.get("/profile", response_model=GuardOut)
async def get_guard_profile(
    current_guard: Annotated[Guard, Depends(get_current_guard)],
    db: Session = Depends(get_db)
):
    """
    Retrieve the profile of the currently authenticated guard.
    """
    # Récupérer les données complètes du gardien depuis la base de données
    guard = db.query(Guard).filter(Guard.id == current_guard.id).first()
    if not guard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Profil du gardien non trouvé"
        )
    return guard


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    # Vérifiez si le numéro de téléphone existe dans la base de données
    owner = db.query(Guard).filter(Guard.phone_number == request.phone_number).first()
    if not owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Numéro de téléphone non trouvé")

    return {"message": "Numéro de téléphone valide. Veuillez saisir votre nouveau mot de passe."}

@router.post("/reset-password", response_model=MessageResponse)
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    # Vérifiez si le numéro de téléphone existe dans la base de données
    owner = db.query(Guard).filter(Guard.phone_number == request.phone_number).first()
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



@router.get("/{guard_id}", response_model=GuardOut)
async def get_guard(guard_id: UUID, db: Session = Depends(get_db)):
    guard = db.query(Guard).filter(Guard.id == guard_id).first()
    if not guard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gardien non trouvé")
    return guard


@router.put("/{guard_id}", response_model=GuardOut)
async def update_guard(guard_id: UUID, guard: GuardUpdate, db: Session = Depends(get_db)):
    db_guard = db.query(Guard).filter(Guard.id == guard_id).first()
    if not db_guard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gardien non trouvé")

    for key, value in guard.dict(exclude_unset=True).items():
        setattr(db_guard, key, value)

    db.commit()
    db.refresh(db_guard)
    return db_guard


@router.delete("/{guard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_guard(guard_id: UUID, db: Session = Depends(get_db)):
    guard = db.query(Guard).filter(Guard.id == guard_id).first()
    if not guard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gardien non trouvé")

    db.delete(guard)
    db.commit()
    return {"message": "Gardien supprimé avec succès"}


@router.get("/{guard_id}/qr-scans", response_model=List[GuardQRScanOut])
async def get_guard_qr_scans(
    guard_id: UUID,
    db: Session = Depends(get_db)
):
    guard = db.query(Guard).filter(Guard.id == guard_id).first()
    if not guard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gardien non trouvé")

    # Récupérez tous les scans de QR codes effectués par ce gardien
    qr_scans = db.query(GuardQRScan).filter(GuardQRScan.guard_id == guard_id).all()

    return qr_scans
    