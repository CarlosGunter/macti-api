import httpx

from app.core.config import settings

url = "https://pruebasm.solucionesatd.com/webservice/rest/server.php"
TOKEN = settings.SMTP_PASS
nuevo_usuario = {
    "username": "nuevo.usuario",
    "password": "Pass123!",
    "firstname": "Nombre",
    "lastname": "Apellido",
    "email": "correo@dominio.com",
}
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Content-Type": "application/x-www-form-urlencoded",
}
data = {
    "wstoken": TOKEN,
    "wsfunction": "core_user_create_users",
    "moodlewsrestformat": "json",
    "users[0][username]": nuevo_usuario["username"],
    "users[0][password]": nuevo_usuario["password"],
    "users[0][firstname]": nuevo_usuario["firstname"],
    "users[0][lastname]": nuevo_usuario["lastname"],
    "users[0][email]": nuevo_usuario["email"],
}

try:
    r = httpx.post(url, data=data, headers=headers, timeout=15)
    r.raise_for_status()  # Lanza error si el código HTTP no es 200
except httpx.HTTPError as e:
    print("Error en la petición:", e)
    exit()

respuesta = r.json()
if "exception" in respuesta:
    print("Error de Moodle:", respuesta["message"])
else:
    print("Usuario creado correctamente:")
    print(respuesta)
