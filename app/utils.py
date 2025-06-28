import qrcode
import base64
from io import BytesIO
from passlib.context import CryptContext
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from datetime import datetime
import requests
import os


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hashed(password: str):
    return pwd_context.hash(password)

def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def generate_qr_content(user_name: str, user_phone: str, user_appartement: str, visitor_name: str, visitor_phone: str, duration_minutes: int) -> str:
    return f"User Name: {user_name}, User Phone: {user_phone}, User Appartement: {user_appartement}, Visitor Name: {visitor_name}, Visitor Phone: {visitor_phone}, Duration: {duration_minutes} minutes"

def generate_qr_code_base64(data: str) -> str:
    qr = qrcode.make(data)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

def generate_pdf(file_path, title, owner_name, report_type, data: dict):
    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    # En-tête du rapport
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, title)

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 70, f"Type: {report_type}")

    c.setFont("Helvetica", 10)
    c.drawString(50, height - 90, f"Propriétaire: {owner_name}")
    c.drawString(50, height - 105, f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    # Résumé selon le type de rapport
    y_position = height - 140
    y_position = add_summary_section(c, data.get('summary', {}), y_position, report_type)

    # Table des données selon le type de rapport
    if 'scans' in data:
        y_position = add_data_table(c, data['scans'], data.get('focus', ''), y_position)

    if report_type == 'activity_report' and 'guard_attendances' in data:
        y_position = add_guard_attendance_table(c, data['guard_attendances'], y_position)

    # Pied de page
    c.drawString(50, 30, "Rapport généré automatiquement.")

    # Conclusion selon le type de rapport
    conclusion = get_conclusion_by_type(report_type, data.get('summary', {}))
    c.drawString(50, 50, conclusion)

    c.save()

def add_summary_section(c, summary, y_position, report_type):
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_position, "Résumé:")
    y_position -= 20

    c.setFont("Helvetica", 10)

    if report_type == "user_report":
        c.drawString(70, y_position, f"Total des scans: {summary.get('total_scans', 0)}")
        y_position -= 15
        c.drawString(70, y_position, f"Visiteurs uniques: {summary.get('unique_users', 0)}")
        y_position -= 15
        c.drawString(70, y_position, f"Moyenne scans/visiteur: {summary.get('avg_scans_per_user', 0):.1f}")
        y_position -= 25

    elif report_type == "qr_code_report":
        c.drawString(70, y_position, f"Total des scans: {summary.get('total_scans', 0)}")
        y_position -= 15
        c.drawString(70, y_position, f"Codes QR uniques: {summary.get('unique_qr_codes', 0)}")
        y_position -= 15
        c.drawString(70, y_position, f"Moyenne scans/QR: {summary.get('avg_scans_per_qr', 0):.1f}")
        y_position -= 25

    elif report_type == "activity_report":
        c.drawString(70, y_position, f"Total des scans: {summary.get('total_scans', 0)}")
        y_position -= 15
        peak_hour = summary.get('peak_hour')
        if peak_hour is not None:
            c.drawString(70, y_position, f"Heure de pointe: {peak_hour}h")
            y_position -= 15
        daily_avg = summary.get('daily_average')
        if daily_avg is not None:
            c.drawString(70, y_position, f"Moyenne quotidienne: {daily_avg:.1f}")
            y_position -= 15
        y_position -= 10

    elif report_type == "security_report":
        c.drawString(70, y_position, f"Total des scans: {summary.get('total_scans', 0)}")
        y_position -= 15
        c.drawString(70, y_position, f"Scans suspects: {summary.get('suspicious_scans', 0)}")
        y_position -= 15
        c.drawString(70, y_position, f"Score de sécurité: {summary.get('security_score', 'N/A')}")
        y_position -= 25

    return y_position

def add_data_table(c, scans, focus, y_position):
    if focus == 'users':
        headers = ["Visiteur", "Téléphone", "Garde", "Heure de scan"]
        data = [headers]
        for scan in scans:
            if hasattr(scan, 'form_data') and scan.form_data and hasattr(scan, 'guard'):
                data.append([
                    getattr(scan.form_data, 'name', 'N/A'),
                    getattr(scan.form_data, 'phone_number', 'N/A'),
                    getattr(scan.guard, 'name', 'N/A'),
                    scan.scanned_at.strftime("%d/%m/%Y %H:%M")
                ])

    elif focus == 'qr_codes':
        headers = ["QR Code", "Visiteur", "Garde", "Heure de scan"]
        data = [headers]
        for scan in scans:
            data.append([
                scan.qr_code_data[:20] + "..." if len(scan.qr_code_data) > 20 else scan.qr_code_data,
                getattr(scan.form_data, 'name', 'N/A'),
                getattr(scan.guard, 'name', 'N/A'),
                scan.scanned_at.strftime("%d/%m/%Y %H:%M")
            ])

    elif focus == 'activity':
        headers = ["Heure", "Visiteur", "Garde", "QR Code"]
        data = [headers]
        for scan in scans:
            data.append([
                scan.scanned_at.strftime("%d/%m/%Y %H:%M"),
                getattr(scan.form_data, 'name', 'N/A'),
                getattr(scan.guard, 'name', 'N/A'),
                scan.qr_code_data[:15] + "..." if len(scan.qr_code_data) > 15 else scan.qr_code_data
            ])

    elif focus == 'security':
        headers = ["Heure", "Visiteur", "Garde", "Status"]
        data = [headers]
        for scan in scans:
            status = "Normal"
            data.append([
                scan.scanned_at.strftime("%d/%m/%Y %H:%M"),
                getattr(scan.form_data, 'name', 'N/A'),
                getattr(scan.guard, 'name', 'N/A'),
                status
            ])

    table = Table(data, colWidths=[120, 120, 100, 100])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
    ]))

    table.wrapOn(c, 50, 400)
    table.drawOn(c, 50, y_position - len(data) * 15)
    return y_position - len(data) * 15 - 20

def add_guard_attendance_table(c, guard_attendances, y_position):
    headers = ["Garde", "Heure de début", "Heure de fin"]
    data = [headers]

    for guard_name, attendances in guard_attendances.items():
        for attendance in attendances:
            data.append([
                guard_name,
                attendance['start_time'].strftime("%d/%m/%Y %H:%M"),
                attendance['end_time'].strftime("%d/%m/%Y %H:%M") if attendance['end_time'] else 'N/A'
            ])

    table = Table(data, colWidths=[120, 120, 120])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
    ]))

    table.wrapOn(c, 50, 400)
    table.drawOn(c, 50, y_position - len(data) * 15)
    return y_position - len(data) * 15 - 20

def get_conclusion_by_type(report_type, summary):
    if report_type == "user_report":
        return f"Analyse utilisateurs: {summary.get('unique_users', 0)} visiteurs uniques identifiés."
    elif report_type == "qr_code_report":
        return f"Analyse QR Codes: {summary.get('unique_qr_codes', 0)} codes différents utilisés."
    elif report_type == "activity_report":
        return f"Analyse d'activité: {summary.get('total_scans', 0)} accès enregistrés."
    elif report_type == "security_report":
        return f"Analyse sécurité: {summary.get('security_score', 'N/A')} - {summary.get('suspicious_scans', 0)} incidents détectés."



# def send_alert_email(to, name, role, resident_name, resident_phone, resident_appartement, alert_details):
#     api_key = os.getenv('SENDINBLUE_API_KEY')
#     url = 'https://api.brevo.com/v3/smtp/email'

#     subject = f"🚨 Alerte : Problème signalé par {resident_name}"
#     html_content = f"""
#     <div>
#         <h2>Bonjour {name},</h2>
#         <p>Une alerte a été signalée par le résident {resident_name} (Tél: {resident_phone}, Appartement: {resident_appartement}).</p>
#         <p><strong>Détails de l'alerte :</strong> {alert_details}</p>
#         <p>Veuillez prendre les mesures nécessaires.</p>
#         <p>Cordialement,<br/>L'équipe de gestion</p>
#     </div>
#     """

#     email_data = {
#         "sender": {
#             "name": "Welqo Alerte",
#             "email": "diallo30amadoukorka@gmail.com"
#         },
#         "to": [
#             {
#                 "email": to
#             }
#         ],
#         "subject": subject,
#         "htmlContent": html_content
#     }

#     headers = {
#         'Content-Type': 'application/json',
#         'api-key': api_key
#     }

#     try:
#         response = requests.post(url, json=email_data, headers=headers)
#         response.raise_for_status()
#         return response.json()
#     except requests.exceptions.RequestException as error:
#         print(f"Erreur lors de l'envoi de l'email à {role} {name} :", error)
#         raise error

