import smtplib
from email.message import EmailMessage
from uuid import uuid4
import sqlite3
from datetime import datetime, timedelta
from dateutil.parser import parse


class EmailService:
    SMTP_HOST = 'smtp.titan.email'
    SMTP_PORT = 587
    SMTP_USER = 'aramirez@solucionesatd.com'
    SMTP_PASS = '17A07n95t%Rmz!'
    FROM_ADDRESS = 'aramirez@solucionesatd.com'
    FROM_NAME = 'MACTI Proto'

    @staticmethod
    def send_validation_email(to_email: str):
        token = str(uuid4())
        fecha_solicitud = datetime.now()
        fecha_expiracion = fecha_solicitud + timedelta(hours=12)
        conn = sqlite3.connect('macti.db')
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO MCT_Validacion (correo, token, fecha_solicitud, fecha_expiracion, bandera)
            VALUES (?, ?, ?, ?, 0)
        """, (to_email, token, fecha_solicitud, fecha_expiracion))

        conn.commit()
        conn.close()
        confirm_link = f"http://localhost:3000/registro/confirmacion?token={token}"
        msg = EmailMessage()
        msg['Subject'] = 'Confirma tu correo'
        msg['From'] = f"{EmailService.FROM_NAME} <{EmailService.FROM_ADDRESS}>"
        msg['To'] = to_email
        msg.set_content(f'Hola!\n\nConfirma tu correo haciendo click aquí: {confirm_link}\n\nGracias! ATT MACTI')
        try:
            with smtplib.SMTP(EmailService.SMTP_HOST, EmailService.SMTP_PORT) as smtp:
                smtp.starttls()
                smtp.login(EmailService.SMTP_USER, EmailService.SMTP_PASS)
                smtp.send_message(msg)
            return {"message": f"Correo enviado a {to_email}", "token": token}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def validate_token(token: str):
        conn = sqlite3.connect("macti.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, correo, fecha_expiracion, bandera FROM MCT_Validacion WHERE token = ?
        """, (token,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return {"success": False, "error": "Token inválido"}

        val_id, correo, fecha_expiracion, bandera = row
        now = datetime.now()

        if bandera == 1:
            conn.close()
            return {"success": False, "error": "Token ya utilizado"}

        if now > datetime.fromisoformat(fecha_expiracion):
            conn.close()
            return {"success": False, "error": "Token expirado"}

        # cursor.execute("UPDATE MCT_Validacion SET bandera = 1 WHERE id = ?", (val_id,))
        # conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "Token válido",
            "data": {
                "id": val_id,
                "correo": correo
            }
        }