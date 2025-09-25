import smtplib
from email.message import EmailMessage
from uuid import uuid4

class EmailService:
    SMTP_HOST = 'smtp.titan.email'
    SMTP_PORT = 587
    SMTP_USER = 'aramirez@solucionesatd.com'
    SMTP_PASS = '17A07n95t%Rmz!'
    FROM_ADDRESS = 'aramirez@solucionesatd.com'
    FROM_NAME = 'MACTI Proto'

    @staticmethod
    def send_validation_email(to_email: str):
        # Al recuperar los daros del usuario, se debe obtener el instituto al que solicita la cuenta y redirigir al link correspondiente
        # Remplazar "institute_id_placeholder" por el ID real del instituto
        institute_id = "institute_id_placeholder"

        token = str(uuid4())
        confirm_link = f"http://localhost:3000/{institute_id}/registro/confirmacion?token={token}"
        msg = EmailMessage()
        msg['Subject'] = 'Confirma tu correo'
        msg['From'] = f"{EmailService.FROM_NAME} <{EmailService.FROM_ADDRESS}>"
        msg['To'] = to_email
        msg.set_content(f'Hola!\n\nConfirma tu correo haciendo click aquí: {confirm_link}\n\nGracias!')

        try:
            with smtplib.SMTP(EmailService.SMTP_HOST, EmailService.SMTP_PORT) as smtp:
                smtp.starttls()
                smtp.login(EmailService.SMTP_USER, EmailService.SMTP_PASS)
                smtp.send_message(msg)
            return {"message": f"Correo enviado a {to_email}", "token": token}
        except Exception as e:
            return {"error": str(e)}
