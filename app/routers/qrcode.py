from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from typing import List

from app.schemas.guard import GuardQRScanOut
from app.schemas.qrcode import QRScanRequest, QRScanResponse
from app.models.data import FormData, Guard, GuardQRScan
from app.postgres_connect import get_db
from app.oauth2 import get_current_guard

router = APIRouter(prefix="/guard-scans", tags=["Guard QR Scans"])

@router.post("/scan", response_model=QRScanResponse)
async def scan_qr_code(
    qr_scan: QRScanRequest,
    db: Session = Depends(get_db),
    current_guard: Guard = Depends(get_current_guard)
):
    # Recherchez le formulaire associé au code QR
    form = db.query(FormData).filter_by(qr_code_data=qr_scan.qr_code_data).first()

    if not form:
        return QRScanResponse(valid=False, message="QR code introuvable")

    if datetime.now() > form.expires_at:
        return QRScanResponse(valid=False, message="QR code expiré")

    # Créez un nouvel enregistrement de scan
    new_scan = GuardQRScan(
        qr_code_data=qr_scan.qr_code_data,
        guard_id=current_guard.id,
        form_data_id=form.id
    )

    db.add(new_scan)
    db.commit()
    db.refresh(new_scan)

    # Récupérez les informations de l'utilisateur et du visiteur
    user_info = {
        "name": form.user.name,
        "phone_number": form.user.phone_number,
        "appartement": form.user.appartement
    }

    visitor_info = {
        "name": form.name,
        "phone_number": form.phone_number
    }

    return QRScanResponse(
        valid=True,
        message="QR code valide",
        user_info=user_info,
        visitor_info=visitor_info,
        duration_minutes=form.duration_minutes
    )


@router.get("/guard/{guard_id}/scans", response_model=List[GuardQRScanOut])
async def get_guard_qr_scans(
    guard_id: UUID,
    db: Session = Depends(get_db)
):
    # Vérifiez si le gardien existe
    guard = db.query(Guard).filter(Guard.id == guard_id).first()
    if not guard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gardien non trouvé")

    # Récupérez tous les scans de QR codes effectués par ce gardien
    qr_scans = db.query(GuardQRScan).filter(GuardQRScan.guard_id == guard_id).all()

    return qr_scans

@router.get("/scan-history", response_model=List[GuardQRScanOut])
async def get_scan_history(
    db: Session = Depends(get_db),
    current_guard: Guard = Depends(get_current_guard)
):
    qr_scans = db.query(GuardQRScan).filter(GuardQRScan.guard_id == current_guard.id).all()

    return qr_scans



@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_qr_scan(
    scan_id: UUID,
    db: Session = Depends(get_db)
):
    scan = db.query(GuardQRScan).filter(GuardQRScan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan non trouvé")

    db.delete(scan)
    db.commit()
    return {"message": "Scan supprimé avec succès"}

