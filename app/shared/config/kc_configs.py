from app.core.config import settings

keycloak_configs = {
    "principal": {
        "url": "https://sso.lamod.unam.mx/auth",
        "realm": "macti3dev",
        "clientId": "fastapi-auth-service",
        "secretPass": settings.KEYCLOAK_ADMIN_CLIENT_SECRET,
    },
    "cuantico": {
        "url": "https://keycloakmacti1.duckdns.org:8443",
        "realm": "Macti4dev",
        "clientId": "fastapi-auth-service",
        "secretPass": settings.Cuantico_ADMIN_CLIENT_SECRET,
    },
    "ciencias": {
        "url": "https://keycloakmacti2.duckdns.org:8444",
        "realm": "Macti4dev",
        "clientId": "fastapi-auth-service",
        "secretPass": settings.Ciencias_ADMIN_CLIENT_SECRET,
    },
    "ingenieria": {
        "url": "https://keycloakmacti3.duckdns.org:8445",
        "realm": "Macti4dev",
        "clientId": "fastapi-auth-service",
        "secretPass": settings.Ingenieria_ADMIN_CLIENT_SECRET,
    },
}
