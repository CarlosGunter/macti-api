from pydantic import field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    KEYCLOAK_SERVER_URL: str = "http://localhost:8080"
    KEYCLOAK_REALM: str = "master"
    KEYCLOAK_ADMIN_CLIENT_ID: str = "fastapi-auth-service"         
    KEYCLOAK_USERNAME: str = "admin"
    KEYCLOAK_PASSWORD: str = "admin"
    KEYCLOAK_ADMIN_CLIENT_SECRET: str = ""

    MOODLE_URL: str = "http://localhost/moodle"
    MOODLE_TOKEN: str = ""

    SMTP_HOST: str = "smtp.titan.email"
    SMTP_PORT: int = 587
    SMTP_USER: str = "aramirez@solucionesatd.com"
    SMTP_PASS: str = ""
    FROM_ADDRESS: str = "aramirez@solucionesatd.com"

    @field_validator("KEYCLOAK_ADMIN_CLIENT_SECRET")
    def check_admin_client_secret(cls, v):
        if not v:
            raise ValueError("KEYCLOAK_ADMIN_CLIENT_SECRET no definido en las variables de entorno")
        if len(v) < 32:
            raise ValueError("KEYCLOAK_ADMIN_CLIENT_SECRET debe tener 32 caracteres")
        return v
    
    @field_validator("MOODLE_TOKEN")
    def check_moodle_token(cls, v):
        if not v:
            raise ValueError("MOODLE_TOKEN no definido en las variables de entorno")
        if len(v) < 32:
            raise ValueError("MOODLE_TOKEN debe tener 32 caracteres")
        return v
    
    @field_validator("SMTP_PASS")
    def check_smtp_pass(cls, v):
        if not v or v.strip() == "":
            raise ValueError("SMTP_PASS no definido en las variables de entorno")
        return v

    class Config:
        env_file = ".env"
        extra = 'ignore'

settings = Settings()