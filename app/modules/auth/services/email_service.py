import smtplib
from email.message import EmailMessage

from app.core.environment import environment


class EmailService:
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
