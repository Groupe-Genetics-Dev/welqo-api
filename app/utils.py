import qrcode
import base64
from io import BytesIO
from passlib.context import CryptContext
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from datetime import datetime

from app.schemas.report import ReportType



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hashed(password: str):
    return pwd_context.hash(password)


def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)



def generate_qr_code_base64(data: str) -> str:
    qr = qrcode.make(data)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def generate_qr_content(user_name: str, user_phone: str, user_appartement: str, visitor_name: str, visitor_phone: str, duration_minutes: int) -> str:
    return f"User Name: {user_name}, User Phone: {user_phone}, User Appartement: {user_appartement}, Visitor Name: {visitor_name}, Visitor Phone: {visitor_phone}, Duration: {duration_minutes} minutes"


def generate_pdf(file_path, title, owner_name, report_type: ReportType, data: dict):
    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    # En-tête du rapport
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, title)
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 70, f"Type : {report_type.value}")

    c.setFont("Helvetica", 10)
    c.drawString(50, height - 90, f"Propriétaire : {owner_name}")
    c.drawString(50, height - 105, f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    # Résumé selon le type de rapport
    y_position = height - 140
    y_position = add_summary_section(c, data['summary'], y_position, report_type)

    # Table des données selon le type de rapport
    y_position = add_data_table(c, data['scans'], data['focus'], y_position)

    # Pied de page
    c.drawString(50, 100, "Rapport généré automatiquement.")
    
    # Conclusion selon le type de rapport
    conclusion = get_conclusion_by_type(report_type, data['summary'])
    c.drawString(50, 85, conclusion)

    c.save()

def add_summary_section(c, summary, y_position, report_type):
    """Ajoute la section résumé selon le type de rapport"""
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_position, "RÉSUMÉ :")
    y_position -= 20

    c.setFont("Helvetica", 10)

    if report_type == ReportType.USER_REPORT:
        c.drawString(70, y_position, f"• Total des scans : {summary.get('total_scans', 0)}")
        y_position -= 15
        c.drawString(70, y_position, f"• Visiteurs uniques : {summary.get('unique_visitors', 0)}")
        y_position -= 15
        c.drawString(70, y_position, f"• Moyenne scans/visiteur : {summary.get('avg_scans_per_visitor', 0):.1f}")
        y_position -= 25

    elif report_type == ReportType.QR_CODE_REPORT:
        c.drawString(70, y_position, f"• Total des scans : {summary.get('total_scans', 0)}")
        y_position -= 15
        c.drawString(70, y_position, f"• Codes QR uniques : {summary.get('unique_qr_codes', 0)}")
        y_position -= 15
        c.drawString(70, y_position, f"• Moyenne scans/QR : {summary.get('avg_scans_per_qr', 0):.1f}")
        y_position -= 25

    elif report_type == ReportType.ACTIVITY_REPORT:
        c.drawString(70, y_position, f"• Total des scans : {summary.get('total_scans', 0)}")
        y_position -= 15
        peak_hour = summary.get('peak_hour')
        if peak_hour is not None:
            c.drawString(70, y_position, f"• Heure de pointe : {peak_hour}h")
            y_position -= 15
        daily_avg = summary.get('daily_average')
        if daily_avg is not None:
            c.drawString(70, y_position, f"• Moyenne quotidienne : {daily_avg:.1f}")
            y_position -= 15
        y_position -= 10

    elif report_type == ReportType.SECURITY_REPORT:
        c.drawString(70, y_position, f"• Total des scans : {summary.get('total_scans', 0)}")
        y_position -= 15
        c.drawString(70, y_position, f"• Scans suspects : {summary.get('suspicious_scans', 0)}")
        y_position -= 15
        c.drawString(70, y_position, f"• Score de sécurité : {summary.get('security_score', 'N/A')}")
        y_position -= 25

    return y_position

def add_data_table(c, scans, focus, y_position):
    """Ajoute le tableau de données selon le focus du rapport"""
    if focus == 'users':
        headers = ["Visiteur", "Email", "Garde", "Heure de scan"]
        data = [headers]
        for scan in scans:
            data.append([
                scan.form_data.name,
                scan.form_data.email,
                scan.guard.name,
                scan.scan_time.strftime("%d/%m/%Y %H:%M")
            ])
            
    elif focus == 'qr_codes':
        headers = ["QR Code", "Visiteur", "Garde", "Heure de scan"]
        data = [headers]
        for scan in scans:
            data.append([
                scan.qr_code_data[:20] + "..." if len(scan.qr_code_data) > 20 else scan.qr_code_data,
                scan.form_data.name,
                scan.guard.name,
                scan.scan_time.strftime("%d/%m/%Y %H:%M")
            ])
            
    elif focus == 'activity':
        headers = ["Heure", "Visiteur", "Garde", "QR Code"]
        data = [headers]
        for scan in scans:
            data.append([
                scan.scan_time.strftime("%d/%m/%Y %H:%M"),
                scan.form_data.name,
                scan.guard.name,
                scan.qr_code_data[:15] + "..." if len(scan.qr_code_data) > 15 else scan.qr_code_data
            ])
            
    elif focus == 'security':
        headers = ["Heure", "Visiteur", "Garde", "Status"]
        data = [headers]
        for scan in scans:
            status = "Normal"  # Vous pouvez ajouter votre logique de détection ici
            data.append([
                scan.scan_time.strftime("%d/%m/%Y %H:%M"),
                scan.form_data.name,
                scan.guard.name,
                status
            ])

    # Créer et dessiner le tableau
    table = Table(data, colWidths=[120, 120, 100, 100])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
    ]))

    table.wrapOn(c, 50, 400)
    table.drawOn(c, 50, y_position - 150)
    
    return y_position - 200

def get_conclusion_by_type(report_type, summary):
    """Retourne une conclusion appropriée selon le type de rapport"""
    if report_type == ReportType.USER_REPORT:
        return f"Analyse utilisateurs : {summary['unique_visitors']} visiteurs uniques identifiés."
    elif report_type == ReportType.QR_CODE_REPORT:
        return f"Analyse QR Codes : {summary['unique_qr_codes']} codes différents utilisés."
    elif report_type == ReportType.ACTIVITY_REPORT:
        return f"Analyse d'activité : {summary['total_scans']} accès enregistrés."
    elif report_type == ReportType.SECURITY_REPORT:
        return f"Analyse sécurité : {summary['security_score']} - {summary['suspicious_scans']} incidents détectés."

        