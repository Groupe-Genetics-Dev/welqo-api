from typing import Annotated, List
from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.schemas.guard import GuardCreate, GuardOut, GuardQRScanOut, GuardUpdate
from app.models.data import Guard, GuardQRScan
from app.postgres_connect import get_db
from app.utils import hashed


router = APIRouter(prefix="/guards", tags=["Guards"])

@router.post("/create-guard", response_model=GuardOut, status_code=status.HTTP_201_CREATED)
async def create_guard(guard: GuardCreate, db: Session = Depends(get_db)):
    new_guard = Guard(
        name=guard.name,
        password=hashed(guard.password),
        phone_number=guard.phone_number
    )

    db.add(new_guard)
    db.commit()
    db.refresh(new_guard)
    return new_guard


@router.get("/all", response_model=List[GuardOut])
async def get_all_guards(db: Session = Depends(get_db)):
    guards = db.query(Guard).all()
    return guards


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

