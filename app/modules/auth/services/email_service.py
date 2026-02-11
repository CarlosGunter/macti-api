"""
Módulo EmailService - Gestión de Notificaciones Salientes

Este servicio centraliza el envío de correos electrónicos mediante el protocolo SMTP.
Se encarga de construir y despachar mensajes de validación que permiten a los usuarios
finalizar su registro mediante un enlace seguro con token UUID. Utiliza TLS para
garantizar que la comunicación con el servidor de correo sea cifrada.
"""

import smtplib
from email.message import EmailMessage

from app.core.environment import environment


class EmailService:
    """
    Servicio encargado de la comunicación vía Email del sistema MACTI.

    Extrae la configuración del servidor (Host, Puerto, Credenciales) directamente
    del objeto global de configuración para asegurar la portabilidad entre entornos.
    """

    SMTP_HOST = environment.SMTP_HOST
    SMTP_PORT = environment.SMTP_PORT
    SMTP_USER = environment.SMTP_USER
    SMTP_PASS = environment.SMTP_PASS
    FROM_ADDRESS = environment.FROM_ADDRESS
    FROM_NAME = "MACTI Proto"

    @staticmethod
    def send_validation_email(
        to_email: str,
        token: str = "",
        subject: str | None = None,
        body: str | None = None,
    ):
        """
        Envía un correo electrónico de validación con un enlace de confirmación.

        Parámetros:
            to_email: Dirección del destinatario.
            token: Identificador único (UUID) para la validación en el front-end.
            subject: Asunto opcional del correo.
            body: Cuerpo opcional del mensaje en texto plano.

        Retorna:
            Un diccionario con el estatus del envío ('success' o 'error').
        """

        # Enlace dinámico que apunta al front-end de Next.js
        # NOTA: En producción, 'localhost:3000' debe ser reemplazado por el dominio real.
        confirm_link = f"http://localhost:3000/registro/confirmacion?token={token}"

        msg = EmailMessage()
        msg["Subject"] = subject or "¡Cuenta Aprobada! Confirma tu correo"
        msg["From"] = f"{EmailService.FROM_NAME} <{EmailService.FROM_ADDRESS}>"
        msg["To"] = to_email

        # Construcción del cuerpo del mensaje
        msg.set_content(
            body
            or f"""
            Hola, tu solicitud de cuenta ha sido aprobada.
            Para finalizar el proceso y establecer tu contraseña, haz click en el siguiente enlace:
            
            {confirm_link}
            
            Este enlace es personal y tiene una vigencia limitada.
            """,
            subtype="plain",
        )

        try:
            """
            Inicia la conexión SMTP con cifrado TLS (Transport Layer Security).
            El uso del bloque 'with' asegura que la conexión se cierre correctamente 
            incluso si ocurre un error durante el envío.
            """
            with smtplib.SMTP(EmailService.SMTP_HOST, EmailService.SMTP_PORT) as smtp:
                smtp.starttls()  # Asegura la conexión usando TLS
                smtp.login(EmailService.SMTP_USER, EmailService.SMTP_PASS)
                smtp.send_message(msg)

            return {
                "success": True,
                "message": f"Correo enviado exitosamente a {to_email}",
                "token": token,
            }

        except Exception as e:
            """Captura errores de autenticación, red o rechazo del servidor SMTP."""
            return {
                "success": False,
                "error": f"Error en el servidor de correo: {str(e)}",
            }
