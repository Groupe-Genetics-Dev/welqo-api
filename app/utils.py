import qrcode
import base64
from io import BytesIO


def generate_qr_code_base64(data: str) -> str:
    qr = qrcode.make(data)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def generate_qr_content(name: str, phone: str, duration_minutes: int) -> str:
    return f"Name: {name} | Phone: {phone} | Duration: {duration_minutes} minutes"

