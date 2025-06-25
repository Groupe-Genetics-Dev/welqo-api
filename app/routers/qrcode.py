from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from app.schemas.qrcode import GuardQRScanOut, QRScanRequest, QRScanResponse, QRScanData, UserInfo, VisitorInfo, QRConfirmRequest, QRConfirmResponse
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
    form = db.query(FormData).filter(FormData.id == qr_scan.form_id).first()

    if not form:
        return QRScanResponse(valid=False, message="QR code non reconnu ou invalide")

    if datetime.now() > form.expires_at:
        return QRScanResponse(valid=False, message=f"QR code expiré depuis le {form.expires_at.strftime('%d/%m/%Y à %H:%M')}")

    if not form.user:
        return QRScanResponse(valid=False, message="Données utilisateur manquantes")

    # Vérifier si le QR code a déjà été scanné et confirmé ou rejeté
    existing_scan = db.query(GuardQRScan).filter(
        GuardQRScan.form_data_id == qr_scan.form_id,
        GuardQRScan.confirmed.isnot(None)
    ).first()

    if existing_scan:
        action = "validé" if existing_scan.confirmed else "rejeté"
        return QRScanResponse(valid=False, message=f"Le code QR est déjà {action}")

    scan_data = QRScanData(
        user=UserInfo(
            name=form.user.name,
            phone_number=form.user.phone_number,
            appartement=form.user.appartement
        ),
        visitor=VisitorInfo(
            name=form.name,
            phone_number=form.phone_number
        ),
        created_at=form.created_at,
        expires_at=form.expires_at,
        form_id=form.id
    )

    return QRScanResponse(valid=True, message="QR code valide - Vérifiez les informations", data=scan_data)

@router.post("/confirm", response_model=QRConfirmResponse)
async def confirm_access(
    confirm_request: QRConfirmRequest,
    db: Session = Depends(get_db),
    current_guard: Guard = Depends(get_current_guard)
):
    form = db.query(FormData).filter(FormData.id == confirm_request.form_id).first()

    if not form:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QR code introuvable")

    if datetime.now() > form.expires_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="QR code expiré - confirmation impossible")

    existing_confirmation = db.query(GuardQRScan).filter(
        GuardQRScan.form_data_id == confirm_request.form_id,
        GuardQRScan.confirmed.is_not(None)
    ).first()

    if existing_confirmation:
        action = "autorisé" if existing_confirmation.confirmed else "refusé"
        return QRConfirmResponse(
            success=False,
            message=f"Accès déjà {action} le {existing_confirmation.scanned_at.strftime('%d/%m/%Y à %H:%M')}",
            scan_id=existing_confirmation.id
        )

    new_scan = GuardQRScan(
        qr_code_data=str(confirm_request.form_id),
        guard_id=current_guard.id,
        form_data_id=confirm_request.form_id,
        confirmed=confirm_request.confirmed,
        scanned_at=datetime.now()
    )

    db.add(new_scan)
    db.commit()
    db.refresh(new_scan)

    action = "autorisé" if confirm_request.confirmed else "refusé"
    message = f"Accès {action} pour {form.name}"

    return QRConfirmResponse(success=True, message=message, scan_id=new_scan.id)

@router.get("/history", response_model=List[GuardQRScanOut])
async def get_scan_history(
    db: Session = Depends(get_db),
    current_guard: Guard = Depends(get_current_guard),
    limit: int = 50
):
    scans = db.query(GuardQRScan).filter(GuardQRScan.guard_id == current_guard.id).order_by(GuardQRScan.scanned_at.desc()).limit(limit).all()

    return [GuardQRScanOut.from_orm_with_details(scan) for scan in scans]

@router.get("/stats", response_model=dict)
async def get_guard_stats(
    db: Session = Depends(get_db),
    current_guard: Guard = Depends(get_current_guard)
):
    today = datetime.now().date()

    today_scans = db.query(GuardQRScan).filter(
        GuardQRScan.guard_id == current_guard.id,
        GuardQRScan.scanned_at >= today
    ).count()

    today_approved = db.query(GuardQRScan).filter(
        GuardQRScan.guard_id == current_guard.id,
        GuardQRScan.scanned_at >= today,
        GuardQRScan.confirmed == True
    ).count()

    today_denied = db.query(GuardQRScan).filter(
        GuardQRScan.guard_id == current_guard.id,
        GuardQRScan.scanned_at >= today,
        GuardQRScan.confirmed == False
    ).count()

    return {
        "today_scans": today_scans,
        "today_approved": today_approved,
        "today_denied": today_denied,
        "guard_name": getattr(current_guard, 'name', "Gardien")
    }

