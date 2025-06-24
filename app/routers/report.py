from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os

from app.models.data import Attendance, FormData, GuardQRScan, Report, Owner, User
from app.postgres_connect import get_db
from app.schemas.report import ReportCreate, ReportOut, StatisticsOut
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
    print("Filtered Data:", filtered_data)  # Log pour vérifier les données

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
        report_type=report_data.report_type
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return report

def get_filtered_data(db: Session, report_type: str, report_data: ReportCreate):
    if report_type == "user_report":
        return get_user_report_data(db, report_data)
    elif report_type == "qr_code_report":
        return get_qr_code_report_data(db, report_data)
    elif report_type == "activity_report":
        return get_activity_report_data(db, report_data)
    elif report_type == "security_report":
        return get_security_report_data(db, report_data)

def get_user_report_data(db: Session, report_data: ReportCreate):
    # Exemple de récupération de données pour un rapport utilisateur
    scans = db.query(GuardQRScan).join(GuardQRScan.form_data).join(GuardQRScan.guard).all()
    return {
        'summary': {
            'total_scans': len(scans),
            'unique_users': len(set(scan.form_data.user_id for scan in scans)),
            'avg_scans_per_user': len(scans) / len(set(scan.form_data.user_id for scan in scans)) if scans else 0
        },
        'scans': scans,
        'focus': 'users'
    }

def get_qr_code_report_data(db: Session, report_data: ReportCreate):
    # Exemple de récupération de données pour un rapport QR code
    scans = db.query(GuardQRScan).join(GuardQRScan.form_data).join(GuardQRScan.guard).all()
    return {
        'summary': {
            'total_scans': len(scans),
            'unique_qr_codes': len(set(scan.qr_code_data for scan in scans)),
            'avg_scans_per_qr': len(scans) / len(set(scan.qr_code_data for scan in scans)) if scans else 0
        },
        'scans': scans,
        'focus': 'qr_codes'
    }

def get_activity_report_data(db: Session, report_data: ReportCreate):
    attendances = db.query(Attendance).join(Attendance.guard).all()

    guard_attendances = {}
    for attendance in attendances:
        guard_name = attendance.guard.name
        if guard_name not in guard_attendances:
            guard_attendances[guard_name] = []
        guard_attendances[guard_name].append({
            'start_time': attendance.start_time,
            'end_time': attendance.end_time
        })

    return {
        'report_type': 'activity_report',
        'period': {
            'from': report_data.date_from,
            'to': report_data.date_to
        },
        'guard_attendances': guard_attendances
    }

def get_security_report_data(db: Session, report_data: ReportCreate):
    # Exemple de récupération de données pour un rapport de sécurité
    scans = db.query(GuardQRScan).join(GuardQRScan.guard).all()
    return {
        'summary': {
            'total_scans': len(scans),
            'suspicious_scans': 0,  # Exemple de valeur
            'security_score': 'Bon'  # Exemple de valeur
        },
        'scans': scans,
        'focus': 'security'
    }

# IMPORTANT: Route spécifique AVANT la route générique avec paramètre
@router.get("/statistics", response_model=StatisticsOut)
def get_statistics(db: Session = Depends(get_db)):
    # Récupérer les statistiques
    total_users = db.query(User).count()
    total_qr_codes = db.query(FormData).count()
    active_qr_codes = db.query(FormData).filter(FormData.expires_at > datetime.now()).count()
    total_scans = db.query(GuardQRScan).count()
    users_this_month = db.query(User).filter(User.created_at >= datetime.now() - timedelta(days=30)).count()
    qr_codes_this_month = db.query(FormData).filter(FormData.created_at >= datetime.now() - timedelta(days=30)).count()

    return {
        "total_users": total_users,
        "total_qr_codes": total_qr_codes,
        "active_qr_codes": active_qr_codes,
        "total_scans": total_scans,
        "users_this_month": users_this_month,
        "qr_codes_this_month": qr_codes_this_month
    }

@router.delete("/delete-report/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(report_id: str, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rapport non trouvé.")

    if os.path.exists(report.file_path):
        try:
            os.remove(report.file_path)
        except OSError as e:
            print(f"Erreur lors de la suppression du fichier: {e}")

    db.delete(report)
    db.commit()

    return {"message": "Rapport supprimé avec succès."}

@router.get("/list/{owner_id}")
def list_reports(owner_id: str, db: Session = Depends(get_db)):
    owner = db.query(Owner).filter(Owner.id == owner_id).first()
    if not owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Propriétaire non trouvé.")

    reports = db.query(Report).filter(Report.owner_id == owner_id).order_by(Report.created_at.desc()).all()
    return reports

@router.get("/{report_id}")
def get_report(report_id: str, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rapport non trouvé.")

    return report

