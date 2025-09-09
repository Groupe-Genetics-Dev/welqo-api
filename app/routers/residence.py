from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from datetime import datetime

from app.postgres_connect import get_db
from app.models.data import Residence
from app.schemas.residence import ResidenceCreate, ResidenceOut

router = APIRouter(
    prefix="/residences",
    tags=["Residences"]
)

# ✅ Créer une résidence
@router.post("/create", response_model=ResidenceOut, status_code=status.HTTP_201_CREATED)
def create_residence(payload: ResidenceCreate, db: Session = Depends(get_db)):
    new_residence = Residence(
        id=uuid4(),
        name=payload.name,
        address=payload.address,
        created_at=datetime.utcnow()
    )
    db.add(new_residence)
    db.commit()
    db.refresh(new_residence)
    return new_residence

# ✅ Récupérer toutes les résidences
@router.get("/", response_model=list[ResidenceOut])
def list_residences(db: Session = Depends(get_db)):
    residences = db.query(Residence).all()
    return residences

# ✅ Récupérer une résidence par ID
@router.get("/{residence_id}", response_model=ResidenceOut)
def get_residence(residence_id: UUID, db: Session = Depends(get_db)):
    residence = db.query(Residence).filter(Residence.id == residence_id).first()
    if not residence:
        raise HTTPException(status_code=404, detail="Résidence non trouvée")
    return residence

# ✅ Modifier une résidence
@router.put("/{residence_id}", response_model=ResidenceOut)
def update_residence(residence_id: UUID, payload: ResidenceCreate, db: Session = Depends(get_db)):
    residence = db.query(Residence).filter(Residence.id == residence_id).first()
    if not residence:
        raise HTTPException(status_code=404, detail="Résidence non trouvée")
    residence.name = payload.name
    residence.address = payload.address
    db.commit()
    db.refresh(residence)
    return residence

# ✅ Supprimer une résidence
@router.delete("/{residence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_residence(residence_id: UUID, db: Session = Depends(get_db)):
    residence = db.query(Residence).filter(Residence.id == residence_id).first()
    if not residence:
        raise HTTPException(status_code=404, detail="Résidence non trouvée")
    db.delete(residence)
    db.commit()

# ✅ Récupérer les résidences d’un propriétaire
@router.get("/owner/{owner_id}", response_model=list[ResidenceOut])
def get_residences_by_owner(owner_id: UUID, db: Session = Depends(get_db)):
    residences = db.query(Residence).join(Residence.owners).filter_by(id=owner_id).all()
    return residences

