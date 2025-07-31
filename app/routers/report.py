import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os

from app.models.data import Attendance, FormData, GuardQRScan, Report, Owner, User, Guard
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

    # Récupérer les données selon le type de rapport, filtrées par résidence
    filtered_data = get_filtered_data(db, report_data.report_type, report_data, owner.residence_id)
    print("Filtered Data:", filtered_data)  # Log pour vérifier

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
        residence_id=owner.residence_id,
        report_type=report_data.report_type
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return report

def get_filtered_data(db: Session, report_type: str, report_data: ReportCreate, residence_id: uuid.UUID):
    if report_type == "user_report":
        return get_user_report_data(db, residence_id)
    elif report_type == "qr_code_report":
        return get_qr_code_report_data(db, residence_id)
    elif report_type == "activity_report":
        return get_activity_report_data(db, report_data, residence_id)
    elif report_type == "security_report":
        return get_security_report_data(db, residence_id)
    return {}

def get_user_report_data(db: Session, residence_id: uuid.UUID):
    scans = db.query(GuardQRScan)\
        .join(GuardQRScan.form_data)\
        .join(FormData.user)\
        .filter(User.residence_id == residence_id)\
        .all()

    unique_users = set(scan.form_data.user_id for scan in scans)
    total_scans = len(scans)

    return {
        'summary': {
            'total_scans': total_scans,
            'unique_users': len(unique_users),
            'avg_scans_per_user': total_scans / len(unique_users) if unique_users else 0
        },
        'scans': scans,
        'focus': 'users'
    }

def get_qr_code_report_data(db: Session, residence_id: uuid.UUID):
    scans = db.query(GuardQRScan)\
        .join(GuardQRScan.form_data)\
        .join(FormData.user)\
        .filter(User.residence_id == residence_id)\
        .all()

    unique_qr_codes = set(scan.qr_code_data for scan in scans)
    total_scans = len(scans)

    return {
        'summary': {
            'total_scans': total_scans,
            'unique_qr_codes': len(unique_qr_codes),
            'avg_scans_per_qr': total_scans / len(unique_qr_codes) if unique_qr_codes else 0
        },
        'scans': scans,
        'focus': 'qr_codes'
    }

def get_activity_report_data(db: Session, report_data: ReportCreate, residence_id: uuid.UUID):
    attendances = db.query(Attendance)\
        .join(Attendance.guard)\
        .filter(Guard.residence_id == residence_id)\
        .all()

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

def get_security_report_data(db: Session, residence_id: uuid.UUID):
    scans = db.query(GuardQRScan)\
        .join(GuardQRScan.guard)\
        .filter(Guard.residence_id == residence_id)\
        .all()

    return {
        'summary': {
            'total_scans': len(scans),
            'suspicious_scans': 0,  # à adapter
            'security_score': 'Bon'  # à adapter
        },
        'scans': scans,
        'focus': 'security'
    }

@router.get("/statistics", response_model=StatisticsOut)
def get_statistics(residence_id: uuid.UUID , 
                   db: Session = Depends(get_db)):
    
    total_users = db.query(User).filter(User.residence_id == residence_id).count()
    total_qr_codes = db.query(FormData).join(FormData.user).filter(User.residence_id == residence_id).count()
    active_qr_codes = db.query(FormData)\
        .join(FormData.user)\
        .filter(FormData.expires_at > datetime.now(), User.residence_id == residence_id).count()
    total_scans = db.query(GuardQRScan)\
        .join(GuardQRScan.form_data)\
        .join(FormData.user)\
        .filter(User.residence_id == residence_id).count()
    users_this_month = db.query(User)\
        .filter(User.created_at >= datetime.now() - timedelta(days=30), User.residence_id == residence_id).count()
    qr_codes_this_month = db.query(FormData)\
        .join(FormData.user)\
        .filter(FormData.created_at >= datetime.now() - timedelta(days=30), User.residence_id == residence_id).count()

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

