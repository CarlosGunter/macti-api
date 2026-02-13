"""
Módulo de Configuración de Keycloak - Proyecto MACTI

Este módulo define la estructura de datos y el mapeo centralizado para la
conexión con las diferentes instancias de Keycloak. Implementa una arquitectura
Multitenant basada en el instituto del usuario, permitiendo que una sola
instancia de la API gestione múltiples reinos (Realms) y servidores de autenticación.
"""

from dataclasses import dataclass

from app.core.environment import environment
from app.shared.enums.institutes_enum import InstitutesEnum


@dataclass
class DCKeycloakConfig:
    """
    Data Transfer Object (DTO) para la configuración de Keycloak.

    Atributos:
        url: Dirección base del servidor de Keycloak.
        realm: El Reino (Realm) específico dentro de Keycloak para el instituto.
        client_id: Identificador del cliente para la autenticación administrativa.
        secret_pass: Secreto del cliente cargado desde las variables de entorno.
    """

    url: str
    realm: str
    client_id: str
    secret_pass: str


"""
Diccionario maestro de configuraciones de Keycloak.

Vincula cada valor del Enum 'InstitutesEnum' con sus credenciales y endpoints
específicos. Esto permite que el servicio de Keycloak cambie de contexto
de forma dinámica según la procedencia del usuario.
"""
keycloak_configs: dict[InstitutesEnum, DCKeycloakConfig] = {
    InstitutesEnum.PRINCIPAL: DCKeycloakConfig(
        url="https://sso.lamod.unam.mx/auth",
        realm="macti3dev",
        client_id="fastapi-auth-service",
        secret_pass=environment.PRINCIPAL_ADMIN_CLIENT_SECRET,
    ),
    InstitutesEnum.CUANTICO: DCKeycloakConfig(
        url="https://keycloakmacti1.duckdns.org:8443",
        realm="Macti4dev",
        client_id="fastapi-auth-service",
        secret_pass=environment.CUANTICO_ADMIN_CLIENT_SECRET,
    ),
    InstitutesEnum.CIENCIAS: DCKeycloakConfig(
        url="https://keycloakmacti2.duckdns.org:8444",
        realm="Macti4dev",
        client_id="fastapi-auth-service",
        secret_pass=environment.CIENCIAS_ADMIN_CLIENT_SECRET,
    ),
    InstitutesEnum.INGENIERIA: DCKeycloakConfig(
        url="https://keycloakmacti3.duckdns.org:8445",
        realm="Macti4dev",
        client_id="fastapi-auth-service",
        secret_pass=environment.INGENIERIA_ADMIN_CLIENT_SECRET,
    ),
}
