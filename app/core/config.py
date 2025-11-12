from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Princioal
    KEYCLOAK_ADMIN_CLIENT_SECRET: str = ""
    Cuantico_ADMIN_CLIENT_SECRET: str = ""
    Ciencias_ADMIN_CLIENT_SECRET: str = ""
    Ingenieria_ADMIN_CLIENT_SECRET: str = ""

    MOODLE_URL: str = "http://localhost/moodle"
    MOODLE_TOKEN: str = ""

    SMTP_HOST: str = "smtp.titan.email"
    SMTP_PORT: int = 587
    SMTP_USER: str = "aramirez@solucionesatd.com"
    SMTP_PASS: str = ""
    FROM_ADDRESS: str = "aramirez@solucionesatd.com"

    # Agregamos al validaor de la llave secreta las variales de las otras 3

    @field_validator(
        "KEYCLOAK_ADMIN_CLIENT_SECRET",
        "Cuantico_ADMIN_CLIENT_SECRET",
        "Ciencias_ADMIN_CLIENT_SECRET",
        "Ingenieria_ADMIN_CLIENT_SECRET",
    )
    @classmethod
    def check_admin_client_secret(cls, v):
        if not v:
            raise ValueError(
                "KEYCLOAK_ADMIN_CLIENT_SECRET no definido en las variables de entorno"
            )
        if len(v) < 32:
            raise ValueError("KEYCLOAK_ADMIN_CLIENT_SECRET debe tener 32 caracteres")
        return v

    @field_validator("MOODLE_TOKEN")
    @classmethod
    def check_moodle_token(cls, v):
        if not v:
            raise ValueError("MOODLE_TOKEN no definido en las variables de entorno")
        if len(v) < 32:
            raise ValueError("MOODLE_TOKEN debe tener 32 caracteres")
        return v

    @field_validator("SMTP_PASS")
    @classmethod
    def check_smtp_pass(cls, v):
        if not v or v.strip() == "":
            raise ValueError("SMTP_PASS no definido en las variables de entorno")
        return v

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
