from dataclasses import dataclass
from typing import Dict

from app.core.config import settings


@dataclass
class KeycloakConfig:
    url: str
    realm: str
    clientId: str
    secretPass: str


keycloak_configs: Dict[str, KeycloakConfig] = {
    "principal": KeycloakConfig(
        url=settings.KEYCLOAK_SERVER_URL,
        realm=settings.KEYCLOAK_REALM,
        clientId=settings.KEYCLOAK_ADMIN_CLIENT_ID,
        secretPass=settings.KEYCLOAK_ADMIN_CLIENT_SECRET,
    ),
    "cuantico": KeycloakConfig(
        url=settings.Cuantico_SERVER_URL,
        realm=settings.Cuantico_REALM,
        clientId=settings.Cuantico_ADMIN_CLIENT_ID,
        secretPass=settings.Cuantico_ADMIN_CLIENT_SECRET,
    ),
    "ciencias": KeycloakConfig(
        url=settings.Ciencias_SERVER_URL,
        realm=settings.Ciencias_REALM,
        clientId=settings.Ciencias_ADMIN_CLIENT_ID,
        secretPass=settings.Ciencias_ADMIN_CLIENT_SECRET,
    ),
    "ingenieria": KeycloakConfig(
        url=settings.Ingenieria_SERVER_URL,
        realm=settings.Ingenieria_REALM,
        clientId=settings.Ingenieria_ADMIN_CLIENT_ID,
        secretPass=settings.Ingenieria_ADMIN_CLIENT_SECRET,
    ),
}
