import smtplib
import sqlite3
from datetime import datetime, timedelta
from email.message import EmailMessage
from uuid import uuid4

from fastapi import HTTPException

from app.core.config import settings


class EmailService:
    SMTP_HOST = settings.SMTP_HOST
    SMTP_PORT = settings.SMTP_PORT
    SMTP_USER = settings.SMTP_USER
    SMTP_PASS = settings.SMTP_PASS
    FROM_ADDRESS = settings.FROM_ADDRESS
    FROM_NAME = "MACTI Proto"

    @staticmethod
    def generate_and_save_token(to_email: str):
        token = str(uuid4())
        fecha_solicitud = datetime.now()
        fecha_expiracion = fecha_solicitud + timedelta(hours=12)

        try:
            conn = sqlite3.connect("macti.db")
            cursor = conn.cursor()
            # cursor.execute("DELETE FROM MCT_Validacion WHERE email = ?", (to_email,))
            # Primero lo que hago es buscar el id de la cuenta existennte por el email
            cursor.execute(
                "SELECT id FROM account_requests WHERE email = ?", (to_email,)
            )
            row = cursor.fetchone()
            account_id = row[0] if row else None
            cursor.execute("SELECT id FROM MCT_Validacion WHERE email = ?", (to_email,))
            valid_row = cursor.fetchone()

            if valid_row:
                # Actualizar registro existente
                cursor.execute(
                    """
                    UPDATE MCT_Validacion
                    SET token = ?, fecha_solicitud = ?, fecha_expiracion = ?, account_id = ?
                    WHERE email = ?
                """,
                    (token, fecha_solicitud, fecha_expiracion, account_id, to_email),
                )
            else:
                # Insertar nuevo registro
                cursor.execute(
                    """
                    INSERT INTO MCT_Validacion (account_id, email, token, fecha_solicitud, fecha_expiracion, bandera)
                    VALUES (?, ?, ?, ?, ?, 0)
                """,
                    (account_id, to_email, token, fecha_solicitud, fecha_expiracion),
                )

            conn.commit()
            return {"success": True, "token": token}
        except sqlite3.Error as e:
            return {"success": False, "error": f"Error en BD: {e}"}
        finally:
            conn_obj = locals().get("conn", None)
            if conn_obj is not None:
                close_method = getattr(conn_obj, "close", None)
                if callable(close_method):
                    try:
                        close_method()
                    except Exception:
                        # Ignorar errores al cerrar la conexión
                        pass
            conn_obj = locals().get("conn", None)
            if conn_obj is not None:
                close_method = getattr(conn_obj, "close", None)
                if callable(close_method):
                    try:
                        close_method()
                    except Exception:
                        # Ignorar errores al cerrar la conexión
                        pass

    @staticmethod
    def send_validation_email(
        to_email: str,
        subject: str | None = None,
        body: str | None = None,
        generate_token: bool = True,
    ):
        token = None
        confirm_link = ""

        if generate_token:
            token_result = EmailService.generate_and_save_token(to_email)
            if not token_result["success"]:
                return {"success": False, "error": token_result["error"]}
            token = token_result["token"]
            confirm_link = f"http://localhost:3000/registro/confirmacion?token={token}"

        msg = EmailMessage()
        msg["Subject"] = subject or "¡Cuenta Aprobada! Confirma tu correo"
        msg["From"] = f"{EmailService.FROM_NAME} <{EmailService.FROM_ADDRESS}>"
        msg["To"] = to_email
        msg.set_content(
            body
            or f"""
            Hola, tu solicitud de cuenta ha sido aprobada.
            Para finalizar el proceso haz click en el siguiente enlace: {confirm_link}
            """,
            subtype="plain",
        )

        try:
            with smtplib.SMTP(EmailService.SMTP_HOST, EmailService.SMTP_PORT) as smtp:
                smtp.starttls()
                smtp.login(EmailService.SMTP_USER, EmailService.SMTP_PASS)
                smtp.send_message(msg)
            return {
                "success": True,
                "message": f"Correo enviado a {to_email}",
                "token": token,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def validate_token(token: str):
        try:
            conn = sqlite3.connect("macti.db")
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT email, fecha_expiracion, bandera 
                FROM MCT_Validacion 
                WHERE token = ?
            """,
                (token,),
            )
            result = cursor.fetchone()

            if not result:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error_code": "TOKEN_INVALIDO",
                        "message": "Token inválido",
                    },
                )

            email, fecha_expiracion, bandera = result
            fecha_expiracion = datetime.fromisoformat(fecha_expiracion)

            if datetime.now() > fecha_expiracion:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error_code": "TOKEN_EXPIRADO",
                        "message": "El token ha expirado",
                    },
                )

            # NO se cambia bandera aquí
            # Retonar id
            cursor.execute("SELECT id FROM account_requests WHERE email = ?", (email,))
            user_row = cursor.fetchone()

            if not user_row:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error_code": "NO_ENCONTRADO",
                        "message": "No se encontró un usuario con este correo",
                    },
                )

            user_id = user_row[0]

            return {"id": user_id, "email": email}

        except sqlite3.Error as e:
            raise HTTPException(
                status_code=503,
                detail={
                    "error_code": "DB_ERROR",
                    "message": f"Error de base de datos: {e}",
                },
            )

        except HTTPException as httpe:
            raise httpe

        finally:
            conn_obj = locals().get("conn", None)
            if conn_obj is not None:
                close_method = getattr(conn_obj, "close", None)
                if callable(close_method):
                    try:
                        close_method()
                    except Exception:
                        # Ignorar errores al cerrar la conexión
                        pass
