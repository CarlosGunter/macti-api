import smtplib
from email.message import EmailMessage
from uuid import uuid4
import sqlite3
from datetime import datetime, timedelta
from app.core.config import settings

class EmailService:
    SMTP_HOST = settings.SMTP_HOST
    SMTP_PORT = settings.SMTP_PORT
    SMTP_USER = settings.SMTP_USER
    SMTP_PASS = settings.SMTP_PASS
    FROM_ADDRESS = settings.FROM_ADDRESS
    FROM_NAME = 'MACTI Proto'

    @staticmethod
    def generate_and_save_token(to_email: str, institute: str):
        """
        Genera un token UUID, lo guarda en la base de datos junto con la fecha de solicitud,
        expiración y el instituto.
        """
        token = str(uuid4())
        fecha_solicitud = datetime.now()
        fecha_expiracion = fecha_solicitud + timedelta(hours=12)

        try:
            conn = sqlite3.connect('macti.db')
            cursor = conn.cursor()

            # Elimina cualquier token anterior del mismo email
            cursor.execute("DELETE FROM MCT_Validacion WHERE email = ?", (to_email,))

            # Inserta nuevo token
            cursor.execute("""
                INSERT INTO MCT_Validacion (email, token, fecha_solicitud, fecha_expiracion, bandera, institute)
                VALUES (?, ?, ?, ?, 0, ?)
            """, (to_email, token, fecha_solicitud, fecha_expiracion, institute))

            conn.commit()
            return {"success": True, "token": token}
        except sqlite3.Error as e:
            return {"success": False, "error": f"Error en BD: {e}"}
        finally:
            if 'conn' in locals():
                conn.close()

    @staticmethod
    def send_validation_email(to_email: str, institute: str, subject: str = None, body: str = None, generate_token: bool = True):
        """
        Envía un correo de validación. Genera token si generate_token=True.
        """
        token = None
        confirm_link = ""

        if generate_token:
            token_result = EmailService.generate_and_save_token(to_email, institute)
            if not token_result["success"]:
                return {"success": False, "error": token_result["error"]}
            token = token_result["token"]
            confirm_link = f"http://localhost:3000/registro/confirmacion?token={token}"

        msg = EmailMessage()
        msg['Subject'] = subject or '¡Cuenta Aprobada! Confirma tu correo'
        msg['From'] = f"{EmailService.FROM_NAME} <{EmailService.FROM_ADDRESS}>"
        msg['To'] = to_email
        msg.set_content(body or f"""
            Hola, tu solicitud de cuenta ha sido aprobada.
            Para finalizar el proceso haz click en el siguiente enlace: {confirm_link}
            """, subtype='plain')

        try:
            with smtplib.SMTP(EmailService.SMTP_HOST, EmailService.SMTP_PORT) as smtp:
                smtp.starttls()
                smtp.login(EmailService.SMTP_USER, EmailService.SMTP_PASS)
                smtp.send_message(msg)
            return {"success": True, "message": f"Correo enviado a {to_email}", "token": token}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def validate_token(token: str):
        """
        Valida que el token exista y no haya expirado. Retorna el email y el user_id.
        """
        try:
            conn = sqlite3.connect('macti.db')
            cursor = conn.cursor()

            cursor.execute("""
                SELECT email, fecha_expiracion, bandera 
                FROM MCT_Validacion 
                WHERE token = ?
            """, (token,))
            result = cursor.fetchone()

            if not result:
                return {"success": False, "message": "Token no encontrado o inválido"}

            email, fecha_expiracion, bandera = result
            fecha_expiracion = datetime.fromisoformat(fecha_expiracion)

            if datetime.now() > fecha_expiracion:
                return {"success": False, "message": "El token ha expirado"}

            # Obtener id del usuario
            cursor.execute("SELECT id FROM account_requests WHERE email = ?", (email,))
            user_row = cursor.fetchone()
            if not user_row:
                return {"success": False, "error": "User not found"}

            user_id = user_row[0]

            return {
                "success": True,
                "message": "Token válido",
                "data": {"id": user_id, "email": email}
            }

        except sqlite3.Error as e:
            return {"success": False, "message": f"Error de base de datos: {e}"}
        finally:
            if 'conn' in locals():
                conn.close()
