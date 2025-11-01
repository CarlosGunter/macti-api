import smtplib
from email.message import EmailMessage

msg = EmailMessage()
msg["Subject"] = "Test correo"
msg["From"] = "MACTI Proto <aramirez@solucionesatd.com>"
msg["To"] = "the.captain312@gmail.com"
msg.set_content("Hola bro, este es un test")

with smtplib.SMTP("smtp.titan.email", 587) as smtp:
    smtp.starttls()
    smtp.login("aramirez@solucionesatd.com", "17A07n95t%Rmz!")
    smtp.send_message(msg)
