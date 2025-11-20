from dataclasses import dataclass

from app.core.config import settings
from app.shared.enums.institutes_enum import InstitutesEnum


@dataclass
class DCKeycloakConfig:
    url: str
    realm: str
    client_id: str
    secret_pass: str


keycloak_configs: dict[InstitutesEnum, DCKeycloakConfig] = {
    InstitutesEnum.PRINCIPAL: DCKeycloakConfig(
        url="https://sso.lamod.unam.mx/auth",
        realm="macti3dev",
        client_id="fastapi-auth-service",
        secret_pass=settings.KEYCLOAK_ADMIN_CLIENT_SECRET,
    ),
    InstitutesEnum.CUANTICO: DCKeycloakConfig(
        url="https://keycloakmacti1.duckdns.org:8443",
        realm="Macti4dev",
        client_id="fastapi-auth-service",
        secret_pass=settings.Cuantico_ADMIN_CLIENT_SECRET,
    ),
    InstitutesEnum.CIENCIAS: DCKeycloakConfig(
        url="https://keycloakmacti2.duckdns.org:8444",
        realm="Macti4dev",
        client_id="fastapi-auth-service",
        secret_pass=settings.Ciencias_ADMIN_CLIENT_SECRET,
    ),
    InstitutesEnum.INGENIERIA: DCKeycloakConfig(
        url="https://keycloakmacti3.duckdns.org:8445",
        realm="Macti4dev",
        client_id="fastapi-auth-service",
        secret_pass=settings.Ingenieria_ADMIN_CLIENT_SECRET,
    ),
}
