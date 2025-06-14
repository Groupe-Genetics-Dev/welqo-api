from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import os

from app.models.data import FormData, Report, GuardQRScan, Owner, User
from app.postgres_connect import get_db
from app.schemas.report import ReportCreate, ReportOut, ReportType
from app.utils import generate_pdf

router = APIRouter(prefix="/reports", tags=["Reports"])

REPORTS_DIR = "generated_reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

@router.post("/create-reports", response_model=ReportOut)
def create_report(report_data: ReportCreate, db: Session = Depends(get_db)):
    owner = db.query(Owner).filter(Owner.id == report_data.owner_id).first()
    if not owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Propriétaire non trouvé.")

    # Récupérer les données selon le type de rapport
    filtered_data = get_filtered_data(db, report_data.report_type, report_data)

    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{report_data.title.replace(' ', '_')}.pdf"
    file_path = os.path.join(REPORTS_DIR, filename)

    generate_pdf(
        file_path=file_path,
        title=report_data.title,
        owner_name=owner.name,
        report_type=report_data.report_type,
        data=filtered_data
    )

    report = Report(
        title=report_data.title,
        file_path=file_path,
        owner_id=owner.id,
        report_type=report_data.report_type  # Assurez-vous que cette valeur est correcte
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return report

def get_filtered_data(db: Session, report_type: ReportType, report_data: ReportCreate):
    """Récupère les données filtrées selon le type de rapport"""
    base_query = db.query(GuardQRScan).join(GuardQRScan.guard).join(GuardQRScan.form_data)

    # Filtrer par date si spécifié
    if report_data.date_from:
        base_query = base_query.filter(GuardQRScan.scan_time >= report_data.date_from)
    if report_data.date_to:
        base_query = base_query.filter(GuardQRScan.scan_time <= report_data.date_to)

    if report_type == ReportType.USER_REPORT:
        return {
            'scans': base_query.all(),
            'focus': 'users',
            'summary': get_user_summary(base_query)
        }

    elif report_type == ReportType.QR_CODE_REPORT:
        return {
            'scans': base_query.all(),
            'focus': 'qr_codes',
            'summary': get_qr_code_summary(base_query)
        }

    elif report_type == ReportType.ACTIVITY_REPORT:
        return {
            'scans': base_query.all(),
            'focus': 'activity',
            'summary': get_activity_summary(base_query)
        }

    elif report_type == ReportType.SECURITY_REPORT:
        return {
            'scans': base_query.all(),
            'focus': 'security',
            'summary': get_security_summary(base_query)
        }

def get_user_summary(query):
    """Statistiques pour le rapport utilisateur"""
    scans = query.all()
    unique_visitors = len(set(scan.form_data.email for scan in scans))
    return {
        'total_scans': len(scans),
        'unique_visitors': unique_visitors,
        'avg_scans_per_visitor': len(scans) / unique_visitors if unique_visitors > 0 else 0
    }

def get_qr_code_summary(query):
    """Statistiques pour le rapport QR Code"""
    scans = query.all()
    unique_qr_codes = len(set(scan.qr_code_data for scan in scans))
    return {
        'total_scans': len(scans),
        'unique_qr_codes': unique_qr_codes,
        'avg_scans_per_qr': len(scans) / unique_qr_codes if unique_qr_codes > 0 else 0
    }

def get_activity_summary(query):
    """Statistiques pour le rapport d'activité"""
    scans = query.all()
    if not scans:
        return {'total_scans': 0}

    hours = [scan.scan_time.hour for scan in scans]
    from collections import Counter
    hour_counts = Counter(hours)
    peak_hour = hour_counts.most_common(1)[0][0] if hour_counts else None

    return {
        'total_scans': len(scans),
        'peak_hour': peak_hour,
        'daily_average': len(scans) / 7
    }

def get_security_summary(query):
    """Statistiques pour le rapport de sécurité"""
    scans = query.all()
    suspicious_scans = []

    return {
        'total_scans': len(scans),
        'suspicious_scans': len(suspicious_scans),
        'security_score': 'Bon' if len(suspicious_scans) == 0 else 'Attention'
    }

@router.delete("/delete-report/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(report_id: str, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rapport non trouvé.")

    if os.path.exists(report.file_path):
        os.remove(report.file_path)

    db.delete(report)
    db.commit()

    return {"message": "Rapport supprimé avec succès."}


@router.get("/statistics")
def get_global_statistics(db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    total_qr_codes = db.query(FormData).count()
    active_qr_codes = db.query(FormData).filter(FormData.expires_at > datetime.now()).count()
    total_scans = db.query(GuardQRScan).count()

    return {
        "total_users": total_users,
        "total_qr_codes": total_qr_codes,
        "active_qr_codes": active_qr_codes,
        "total_scans": total_scans
    }

