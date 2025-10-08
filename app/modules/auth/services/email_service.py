import smtplib
from email.message import EmailMessage
from uuid import uuid4
import sqlite3
from datetime import datetime, timedelta

class EmailService:
    SMTP_HOST = 'smtp.titan.email'
    SMTP_PORT = 587
    SMTP_USER = 'aramirez@solucionesatd.com'
    SMTP_PASS = '17A07n95t%Rmz!'
    FROM_ADDRESS = 'aramirez@solucionesatd.com'
    FROM_NAME = 'MACTI Proto'

    @staticmethod
    def send_validation_email(to_email: str):
        """
        Envía un correo de validación y guarda el token en la base de datos.
        """
        token = str(uuid4())
        fecha_solicitud = datetime.now()
        fecha_expiracion = fecha_solicitud + timedelta(hours=12)

        try:
            conn = sqlite3.connect('macti.db')
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO MCT_Validacion (email, token, fecha_solicitud, fecha_expiracion, bandera)
                VALUES (?, ?, ?, ?, 0)
            """, (to_email, token, fecha_solicitud, fecha_expiracion))

            conn.commit()
        except sqlite3.Error as e:
            print(f"Error al insertar token en BD: {e}")
            return {"error": f"Error en base de datos: {e}"}
        except Exception as e:
            print(f"Error inesperado en BD: {e}")
            return {"error": str(e)}
        finally:
            if 'conn' in locals():
                conn.close()

        confirm_link = f"http://localhost:3000/registro/confirmacion?token={token}"
        msg = EmailMessage()
        msg['Subject'] = 'Confirma tu correo'
        msg['From'] = f"{EmailService.FROM_NAME} <{EmailService.FROM_ADDRESS}>"
        msg['To'] = to_email
        msg.set_content(f'Hola!\n\nConfirma tu correo haciendo click aquí: {confirm_link}\n\nGracias!\n\nATT: MACTI')

        try:
            with smtplib.SMTP(EmailService.SMTP_HOST, EmailService.SMTP_PORT) as smtp:
                smtp.starttls()
                smtp.login(EmailService.SMTP_USER, EmailService.SMTP_PASS)
                smtp.send_message(msg)
            print(f"📧 Correo enviado correctamente a {to_email}")
            return {"message": f"Correo enviado a {to_email}", "token": token}
        except smtplib.SMTPException as e:
            print(f"Error SMTP al enviar correo: {e}")
            return {"error": f"Fallo al enviar correo: {e}"}
        except Exception as e:
            print(f"Error inesperado al enviar correo: {e}")
            return {"error": str(e)}

    @staticmethod
    def validate_token(token: str):
        """
        Valida el token de correo y devuelve el usuario asociado.
        """
        try:
            conn = sqlite3.connect("macti.db")
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, email, fecha_expiracion, bandera FROM MCT_Validacion WHERE token = ?
            """, (token,))
            row = cursor.fetchone()

            if not row:
                return {"success": False, "error": "Token inválido"}

            val_id, email, fecha_expiracion, bandera = row
            now = datetime.now()

            if bandera == 1:
                return {"success": False, "error": "Token ya utilizado"}

            # Conversión segura de la fecha
            try:
                fecha_exp = datetime.fromisoformat(fecha_expiracion)
            except Exception:
                fecha_exp = datetime.strptime(fecha_expiracion, "%Y-%m-%d %H:%M:%S")

            if now > fecha_exp:
                return {"success": False, "error": "Token expirado"}

            # Buscar al usuario por email
            cursor.execute("SELECT id FROM account_requests WHERE email = ?", (email,))
            user_row = cursor.fetchone()

            if not user_row:
                return {"success": False, "error": "Usuario no encontrado"}

            user_id = user_row[0]

            # Si todo va bien, opcionalmente se puede marcar el token como usado:
            # cursor.execute("UPDATE MCT_Validacion SET bandera = 1 WHERE id = ?", (val_id,))
            # conn.commit()

            return {
                "success": True,
                "message": "Token válido",
                "data": {"id": user_id, "email": email}
            }

        except sqlite3.Error as e:
            print(f"Error al validar token en BD: {e}")
            return {"success": False, "error": f"Error en base de datos: {e}"}
        except Exception as e:
            print(f"Error inesperado en validación: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if 'conn' in locals():
                conn.close()
