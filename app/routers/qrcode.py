from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
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
    """
    Scan un QR code et retourne les informations du visiteur
    
    Workflow:
    1. Frontend scanne le QR code (image) et extrait le texte
    2. Envoie le texte à cet endpoint
    3. Reçoit les données du visiteur pour affichage
    """
    
    # Chercher le formulaire associé au QR code
    form = db.query(FormData).filter(
        FormData.qr_code_data == qr_scan.qr_code_data
    ).first()
    
    if not form:
        return QRScanResponse(
            valid=False, 
            message="QR code non reconnu ou invalide"
        )
    
    # Vérifier l'expiration
    now = datetime.now()
    if now > form.expires_at:
        return QRScanResponse(
            valid=False, 
            message=f"QR code expiré depuis le {form.expires_at.strftime('%d/%m/%Y à %H:%M')}"
        )
    
    # Vérifier si le formulaire a un utilisateur associé
    if not form.user:
        return QRScanResponse(
            valid=False, 
            message="Données utilisateur manquantes"
        )
    
    # Construire la réponse avec toutes les données nécessaires
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
        expires_at=form.expires_at.isoformat(),
        form_id=str(form.id)
    )
    
    return QRScanResponse(
        valid=True,
        message="QR code valide - Vérifiez les informations",
        data=scan_data
    )

@router.post("/confirm", response_model=QRConfirmResponse)
async def confirm_access(
    confirm_request: QRConfirmRequest,
    db: Session = Depends(get_db),
    current_guard: Guard = Depends(get_current_guard)
):
    """
    Confirme ou refuse l'accès après validation visuelle
    
    Workflow:
    1. Le gardien vérifie visuellement les informations affichées
    2. Confirme ou refuse l'accès
    3. L'action est enregistrée en base
    """
    
    try:
        # Re-vérifier le QR code (sécurité)
        form = db.query(FormData).filter(
            FormData.qr_code_data == confirm_request.qr_code_data
        ).first()
        
        if not form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="QR code introuvable"
            )
        
        # Vérifier l'expiration (au moment de la confirmation)
        if datetime.now() > form.expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="QR code expiré - confirmation impossible"
            )
        
        # Vérifier s'il n'y a pas déjà une confirmation pour ce QR code
        existing_confirmation = db.query(GuardQRScan).filter(
            GuardQRScan.qr_code_data == confirm_request.qr_code_data,
            GuardQRScan.confirmed.is_not(None)  # Déjà confirmé ou refusé
        ).first()
        
        if existing_confirmation:
            action = "autorisé" if existing_confirmation.confirmed else "refusé"
            return QRConfirmResponse(
                success=False,
                message=f"Accès déjà {action} le {existing_confirmation.scanned_at.strftime('%d/%m/%Y à %H:%M')}",
                scan_id=str(existing_confirmation.id)
            )
        
        # Créer l'enregistrement de confirmation
        new_scan = GuardQRScan(
            qr_code_data=confirm_request.qr_code_data,
            guard_id=current_guard.id,
            form_data_id=form.id,
            confirmed=confirm_request.confirmed,
            scanned_at=datetime.now()
        )
        
        db.add(new_scan)
        db.commit()
        db.refresh(new_scan)
        
        # Message de confirmation
        action = "autorisé" if confirm_request.confirmed else "refusé"
        message = f"Accès {action} pour {form.name}"
        
        return QRConfirmResponse(
            success=True,
            message=message,
            scan_id=str(new_scan.id)
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la confirmation: {str(e)}"
        )

@router.get("/history", response_model=List[dict])
async def get_scan_history(
    db: Session = Depends(get_db),
    current_guard: Guard = Depends(get_current_guard),
    limit: int = 50
):
    """
    Historique des scans du gardien connecté
    """
    scans = db.query(GuardQRScan).filter(
        GuardQRScan.guard_id == current_guard.id
    ).order_by(
        GuardQRScan.scanned_at.desc()
    ).limit(limit).all()
    
    history = []
    for scan in scans:
        scan_info = {
            "id": str(scan.id),
            "scanned_at": scan.scanned_at.isoformat(),
            "confirmed": scan.confirmed,
            "status": "Autorisé" if scan.confirmed else "Refusé" if scan.confirmed is False else "En attente",
            "qr_code_data": scan.qr_code_data
        }
        
        # Ajouter les détails du formulaire si disponible
        if scan.form_data:
            scan_info.update({
                "visitor_name": scan.form_data.name,
                "visitor_phone": scan.form_data.phone_number,
                "resident_name": scan.form_data.user.name if scan.form_data.user else None,
                "resident_apartment": scan.form_data.user.appartement if scan.form_data.user else None,
                "expires_at": scan.form_data.expires_at.isoformat()
            })
        
        history.append(scan_info)
    
    return history

@router.get("/stats", response_model=dict)
async def get_guard_stats(
    db: Session = Depends(get_db),
    current_guard: Guard = Depends(get_current_guard)
):
    """
    Statistiques des scans du gardien
    """
    today = datetime.now().date()
    
    # Scans d'aujourd'hui
    today_scans = db.query(GuardQRScan).filter(
        GuardQRScan.guard_id == current_guard.id,
        GuardQRScan.scanned_at >= today
    ).count()
    
    # Accès autorisés aujourd'hui
    today_approved = db.query(GuardQRScan).filter(
        GuardQRScan.guard_id == current_guard.id,
        GuardQRScan.scanned_at >= today,
        GuardQRScan.confirmed == True
    ).count()
    
    # Accès refusés aujourd'hui
    today_denied = db.query(GuardQRScan).filter(
        GuardQRScan.guard_id == current_guard.id,
        GuardQRScan.scanned_at >= today,
        GuardQRScan.confirmed == False
    ).count()
    
    return {
        "today_scans": today_scans,
        "today_approved": today_approved,
        "today_denied": today_denied,
        "guard_name": current_guard.name if hasattr(current_guard, 'name') else "Gardien"
    }

