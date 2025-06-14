import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from typing import List
from uuid import UUID
from app.models.data import Owner, Report
from app.schemas.owner import OwnerCreate, OwnerOut
from app.postgres_connect import get_db
from app.schemas.report import ReportOut
from app.oauth2 import get_current_owner
from app.utils import hashed


router = APIRouter(prefix="/owners", tags=["Owners"])

LOGO_DIR = "uploaded_logos"
os.makedirs(LOGO_DIR, exist_ok=True)

@router.post("/create-owner", response_model=OwnerOut)
def create_owner(owner: OwnerCreate, 
                 db: Session = Depends(get_db)):
    
    existing = db.query(Owner).filter(Owner.phone_number == owner.phone_number).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, 
                            detail="Numéro de téléphone déjà utilisé")

    new_owner = Owner(**owner.model_dump())
    new_owner.password = hashed(owner.password)
    db.add(new_owner)
    db.commit()
    db.refresh(new_owner)

    return new_owner


@router.post("/upload-logo", response_model=OwnerOut)
def upload_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_owner: Owner = Depends(get_current_owner)
):
    ext = file.filename.split(".")[-1]
    filename = f"{current_owner.id}_logo.{ext}"
    path = os.path.join(LOGO_DIR, filename)

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    current_owner.logo_path = path
    db.commit()
    db.refresh(current_owner)

    return current_owner


@router.get("/my-reports", response_model=List[ReportOut])
def get_reports_by_owner(
    db: Session = Depends(get_db),
    current_owner: Owner = Depends(get_current_owner)
):
    reports = db.query(Report).filter(Report.owner_id == current_owner.id).all()
    return reports

@router.get("/download/{report_id}", response_class=FileResponse)
def download_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_owner: Owner = Depends(get_current_owner)
):
    report = db.query(Report).filter(Report.id == report_id, Report.owner_id == current_owner.id).first()

    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Rapport non trouvé ou accès non autorisé.")

    if not os.path.exists(report.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail="Fichier PDF introuvable sur le serveur.")

    return FileResponse(
        path=report.file_path,
        filename=os.path.basename(report.file_path),
        media_type='application/pdf'
    )







