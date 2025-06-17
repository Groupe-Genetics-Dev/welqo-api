from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from typing import List
from pydantic import BaseModel
from app.schemas.guard import GuardQRScanOut
from app.schemas.qrcode import QRScanRequest, QRScanResponse, QRScanData, UserInfo, VisitorInfo
from app.models.data import FormData, Guard, GuardQRScan
from app.postgres_connect import get_db
from app.oauth2 import get_current_guard
from app.schemas.qrcode import QRConfirmRequest, QRConfirmResponse

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
    
    # Structure the response data according to frontend expectations
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
        created_at=form.created_at.isoformat(),
        expires_at=form.expires_at.isoformat()
    )
    
    return QRScanResponse(
        valid=True,
        message="QR code valide",
        data=scan_data
    )

@router.post("/confirm", response_model=QRConfirmResponse)
async def confirm_scan(
    confirm_request: QRConfirmRequest,
    db: Session = Depends(get_db),
    current_guard: Guard = Depends(get_current_guard)
):
    try:
        # Find the form data to get the form_data_id
        form = None
        if confirm_request.scan_data and 'data' in confirm_request.scan_data:
            visitor_name = confirm_request.scan_data['data'].get('visitor', {}).get('name')
            visitor_phone = confirm_request.scan_data['data'].get('visitor', {}).get('phone_number')
            
            if visitor_name and visitor_phone:
                form = db.query(FormData).filter(
                    FormData.name == visitor_name,
                    FormData.phone_number == visitor_phone
                ).first()
        
        # Create a new scan record with confirmation status
        new_scan = GuardQRScan(
            qr_code_data=confirm_request.qr_code_data,
            guard_id=current_guard.id,
            form_data_id=form.id if form else None,
            confirmed=confirm_request.confirmed,
            scanned_at=datetime.now()
        )
        
        db.add(new_scan)
        db.commit()
        db.refresh(new_scan)
        
        message = "Accès confirmé" if confirm_request.confirmed else "Accès refusé"
        
        return QRConfirmResponse(
            success=True,
            message=message,
            scan_id=str(new_scan.id)
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la confirmation: {str(e)}"
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
    qr_scans = db.query(GuardQRScan).filter(
        GuardQRScan.guard_id == current_guard.id
    ).order_by(GuardQRScan.scanned_at.desc()).all()
    
    # Convert to detailed schema with form data
    detailed_scans = []
    for scan in qr_scans:
        detailed_scans.append(GuardQRScanOut.from_orm_with_details(scan))
    
    return detailed_scans

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

