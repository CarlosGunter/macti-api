# Módulo de Gestión de Variables de Entorno - Proyecto MACTI
# Este módulo utiliza Pydantic Settings para cargar, tipar y validar todas las
# credenciales y configuraciones sensibles alojadas en el archivo .env.

from pydantic import field_validator
from pydantic_settings import BaseSettings


class EnvironmentConfigs(BaseSettings):
    """
    Clase contenedora de las configuraciones del entorno.

    Define los secretos de administración para los diferentes institutos
    y las configuraciones necesarias para el envío de correos vía SMTP.
    """

    # Secretos de cliente para la administración de Keycloak por instituto
    PRINCIPAL_ADMIN_CLIENT_SECRET: str = ""
    CUANTICO_ADMIN_CLIENT_SECRET: str = ""
    CIENCIAS_ADMIN_CLIENT_SECRET: str = ""
    INGENIERIA_ADMIN_CLIENT_SECRET: str = ""

    # Tokens de acceso a los Web Services de Moodle por instituto
    MOODLE_TOKEN_PRINCIPAL: str = ""
    MOODLE_TOKEN_CUANTICO: str = ""
    MOODLE_TOKEN_CIENCIAS: str = ""
    MOODLE_TOKEN_INGENIERIA: str = ""

    # Configuración del servidor de correo saliente (SMTP)
    SMTP_HOST: str = "smtp.titan.email"
    SMTP_PORT: int = 587
    SMTP_USER: str = "aramirez@solucionesatd.com"
    SMTP_PASS: str = ""
    FROM_ADDRESS: str = "aramirez@solucionesatd.com"

    @field_validator(
        "PRINCIPAL_ADMIN_CLIENT_SECRET",
        "CUANTICO_ADMIN_CLIENT_SECRET",
        "CIENCIAS_ADMIN_CLIENT_SECRET",
        "INGENIERIA_ADMIN_CLIENT_SECRET",
    )
    @classmethod
    def check_admin_client_secret(cls, v):
        """
        Valida que los secretos de Keycloak tengan 32 caracteres.
        """
        if not v:
            raise ValueError(
                "KEYCLOAK_ADMIN_CLIENT_SECRET no definido en las variables de entorno"
            )
        if len(v) != 32:
            raise ValueError("KEYCLOAK_ADMIN_CLIENT_SECRET debe tener 32 caracteres")
        return v

    @field_validator(
        "MOODLE_TOKEN_PRINCIPAL",
        "MOODLE_TOKEN_CUANTICO",
        "MOODLE_TOKEN_CIENCIAS",
        "MOODLE_TOKEN_INGENIERIA",
    )
    @classmethod
    def check_moodle_token(cls, v):
        """
        Valida que los tokens de Moodle tengan 32 caracteres.
        """
        if not v:
            raise ValueError(
                "Token(s) de Moodle no definido en las variables de entorno"
            )
        if len(v) != 32:
            raise ValueError("MOODLE_TOKEN debe tener 32 caracteres")
        return v

    @field_validator("SMTP_PASS")
    @classmethod
    def check_smtp_pass(cls, v):
        """
        Asegura que la contraseña del servidor SMTP no esté vacía.
        """
        if not v or v.strip() == "":
            raise ValueError("SMTP_PASS no definido en las variables de entorno")
        return v

    class Config:
        """
        Configuración interna de Pydantic.
        """

        env_file = ".env"
        extra = "ignore"


# Instancia global de configuración para ser importada en el resto de la app
environment = EnvironmentConfigs()
