"""
Módulo de Verificación de Autenticación
"""

from uuid import UUID

import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError, JWTError
from pydantic import BaseModel, Field, ValidationError

from app.shared.config.kc_configs import keycloak_configs
from app.shared.enums.institutes_enum import InstitutesEnum

# Configuración de seguridad estándar de FastAPI
security = HTTPBearer()
# Caché global para las llaves públicas de Keycloak para optimizar el rendimiento
JWKS_CACHE: dict[InstitutesEnum, dict] = {}


class BearerUserInfo(BaseModel):
    """
    Representación del usuario extraída del Payload del JWT.
    Utiliza alias para mapear los reclamos estándar de OpenID Connect (sub, given_name, etc.).
    """

    kc_id: UUID = Field(..., alias="sub")
    email: str = Field(..., alias="email")
    name: str = Field(..., alias="given_name")
    last_name: str = Field(..., alias="family_name")

    model_config = {"populate_by_name": True}


class KeycloakHeader(BaseModel):
    """Modelo para validar la estructura del encabezado del token JWT."""

    kid: str = Field(..., description="Key ID para identificar la clave de firma")
    typ: str = Field(..., description="Tipo de token, típicamente 'JWT'")
    alg: str = Field(..., description="Algoritmo de firma del token")


async def validate_jwt_token(
    institute: InstitutesEnum,
    credentials=Depends(security),
) -> BearerUserInfo:
    """
    Decodifica y valida firma/claims del token usando las llaves públicas del instituto."""
    jwt_bearer = credentials.credentials
    unverified_header = get_unverified_header(jwt_bearer)

    jwks = await get_jwks_for_institute(institute)
    signing_key = find_signing_key(jwks=jwks, kid=unverified_header.kid)

    return decode_and_validate_token(
        jwt_bearer=jwt_bearer,
        signing_key=signing_key,
        algorithm=unverified_header.alg,
        institute=institute,
    )


def get_unverified_header(token: str) -> KeycloakHeader:
    """Extrae y valida la estructura del encabezado del token."""
    try:
        unverified_header = jwt.get_unverified_header(token)
        unverified_header_parsed = KeycloakHeader.model_validate(unverified_header)
        return unverified_header_parsed
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": "TOKEN_INVALIDO",
                "message": "No se pudo verificar la sesión. Inicia sesión nuevamente.",
            },
        ) from JWTError
    except ValidationError as e:
        print(f"Error de validación del encabezado JWT: {e}")
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": "KID_TOKEN_FALTANTE",
                "message": "No se pudo verificar la sesión.",
            },
        ) from e


async def get_jwks_for_institute(institute: InstitutesEnum) -> dict:
    """
    Recupera el conjunto de llaves públicas (JWKS) desde el servidor de Keycloak.

    Implementa un mecanismo de caché para evitar peticiones redundantes al
    proveedor de identidad en cada validación de token.
    """
    # TODO: Implementar try/catch para manejar errores de conexión o respuestas inválidas
    if institute not in JWKS_CACHE:
        kc = keycloak_configs[institute]
        url = f"{kc.url}/realms/{kc.realm}/protocol/openid-connect/certs"

        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error_code": "KC_JWKS_ERROR",
                        "message": f"No se pudieron obtener JWKS para {institute.value}",
                    },
                )
            JWKS_CACHE[institute] = resp.json()
    return JWKS_CACHE[institute]


def find_signing_key(jwks: dict, kid: str) -> dict:
    """
    Busca la clave de firma específica dentro del JWKS utilizando el 'kid'
    (Key ID) presente en el encabezado del token.
    """
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key

    raise HTTPException(
        status_code=401,
        detail={
            "error_code": "CLAVE_FIRMA_INVALIDA",
            "message": "Clave de firma inválida",
        },
    )


def decode_and_validate_token(
    jwt_bearer: str, signing_key: dict, algorithm: str, institute: InstitutesEnum
) -> BearerUserInfo:
    """
    Decodifica el token JWT usando la clave de firma y valida los reclamos estándar.
    """
    kc = keycloak_configs[institute]
    issuer = f"{kc.url}/realms/{kc.realm}"

    try:
        user_info = jwt.decode(
            token=jwt_bearer,
            key=signing_key,
            algorithms=[algorithm],
            audience="account",
            issuer=issuer,
        )
    except ExpiredSignatureError as e:
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": "TOKEN_EXPIRADO",
                "message": "Tu sesión ha expirado. Inicia sesión nuevamente.",
            },
        ) from e
    except (JWTClaimsError, JWTError, ValidationError) as e:
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": "TOKEN_INVALIDO",
                "message": "Tu sesión no es válida. Inicia sesión nuevamente.",
            },
        ) from e

    try:
        return BearerUserInfo(**user_info)
    except ValidationError:
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": "DECODIFICACION_FALLIDA",
                "message": "Tu sesión no es válida. Inicia sesión nuevamente.",
            },
        ) from ValidationError
