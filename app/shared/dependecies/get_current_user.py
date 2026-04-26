# Módulo de Seguridad y Autenticación - Proyecto MACTI
#
# Este módulo implementa el flujo de validación de tokens JWT (JSON Web Tokens)
# emitidos por Keycloak. Se encarga de:
# 1. Recuperar y cachear las llaves públicas (JWKS) de cada instituto.
# 2. Validar la firma, vigencia y audiencia de los tokens Bearer.
# 3. Sincronizar la identidad de Keycloak con la base de datos local y Moodle.

from uuid import UUID

import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError, JWTError
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.shared.config.kc_configs import keycloak_configs
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.enums.status_enum import AccountStatusEnum
from app.shared.models.auth_model import Auth
from app.shared.models.JIDs_model import JIDs
from app.shared.models.user_profiles_model import UserProfile
from app.shared.services.moodle_service import MoodleService

# Configuración de seguridad estándar de FastAPI
security = HTTPBearer()
ALGORITHM = "RS256"

# Caché global para las llaves públicas de Keycloak para optimizar el rendimiento
JWKS_CACHE: dict[InstitutesEnum, dict] = {}


class CurrentUser(BaseModel):
    """
    Representación del usuario extraída del Payload del JWT.
    Utiliza alias para mapear los reclamos estándar de OpenID Connect (sub, given_name, etc.).
    """

    kc_id: UUID = Field(..., alias="sub")
    email: str = Field(..., alias="email")
    name: str = Field(..., alias="given_name")
    last_name: str = Field(..., alias="family_name")

    model_config = {"populate_by_name": True}


class CurrentUserReturn(CurrentUser):
    """Extensión del modelo de usuario que incluye su vinculación con Moodle."""

    moodle_id: int


class IdentityRepository:
    """Encapsula el acceso de datos de identidad para mantener consultas legibles."""

    def __init__(self, db: Session):
        self.db = db

    def get_moodle_id_by_kc_id(self, kc_id: UUID) -> int | None:
        """Retorna el moodle_id vinculado al kc_id o None si no existe relación."""
        stmt = select(JIDs.moodle_id).where(JIDs.kc_id == kc_id)
        rows = self.db.execute(stmt).scalars().all()

        if len(rows) > 1:
            raise MultipleResultsFound(
                "Se encontró más de un registro JIDs para el mismo kc_id"
            )

        moodle_id = rows[0] if rows else None
        return moodle_id

    def create_identity(
        self, user_info: CurrentUser, institute: InstitutesEnum, moodle_id: int
    ) -> None:
        """Crea identidad local completa (Auth + Profile + JIDs) para usuario sincronizado."""
        auth = Auth(email=user_info.email, institute=institute)
        profile = UserProfile(
            name=user_info.name,
            last_name=user_info.last_name,
            status=AccountStatusEnum.CREATED,
        )
        jids = JIDs(kc_id=user_info.kc_id, moodle_id=moodle_id)

        auth.profile = profile
        auth.jids = jids

        self.db.add(auth)
        self.db.commit()


async def get_current_user(
    institute: InstitutesEnum,
    db: Session = Depends(get_db),
    credentials=Depends(security),
) -> CurrentUserReturn:
    """
    Dependencia de FastAPI que valida el token Bearer y retorna el usuario autenticado.

    Proceso:
    1. Extrae el token y recupera el encabezado.
    2. Valida la firma usando la llave pública del instituto correspondiente.
    3. Verifica que el cliente (azp) sea el autorizado ('next-login').
    4. Resuelve el moodle_id del usuario mediante la base de datos local.
    """
    token = credentials.credentials

    try:
        payload = await decode_and_validate_token(token=token, institute=institute)

        # Validación estricta del cliente originario
        if payload.get("azp") not in ["next-login", "local-next-login"]:
            raise HTTPException(
                status_code=401,
                detail={
                    "error_code": "CLIENTE_INVALIDO",
                    "message": "Cliente no autorizado",
                },
            )

        user_kc_parsed = CurrentUser(**payload)
        moodle_id = await get_user_moodle_id(user_kc_parsed, db, institute)

        # Retorna el objeto unificado con IDs de Keycloak y Moodle
        data = user_kc_parsed.model_dump()
        data["moodle_id"] = moodle_id
        return CurrentUserReturn(**data)

    except ExpiredSignatureError as e:
        raise HTTPException(
            status_code=401,
            detail={"error_code": "TOKEN_EXPIRADO", "message": "Token expirado"},
        ) from e
    except (JWTClaimsError, JWTError, ValidationError) as e:
        raise HTTPException(
            status_code=401, detail={"error_code": "TOKEN_INVALIDO", "message": str(e)}
        ) from e


async def get_user_moodle_id(
    user_info: CurrentUser, db: Session, institute: InstitutesEnum
) -> int:
    """
    Obtiene el ID de Moodle asociado al usuario.
    Si el usuario existe en Keycloak pero no en la BD local de MACTI,
    realiza una sincronización automática ('Just-In-Time Provisioning').
    """
    repository = IdentityRepository(db)

    try:
        moodle_id = repository.get_moodle_id_by_kc_id(user_info.kc_id)
        if moodle_id is not None:
            return moodle_id

        # Caso de sincronización: El usuario existe en Moodle/Keycloak pero no en MACTI.
        # Se recupera su perfil de Moodle y se crea el registro local.
        moodle_id = await get_moodle_id_from_web_service(institute, user_info.email)
        repository.create_identity(
            user_info=user_info, institute=institute, moodle_id=moodle_id
        )
        return moodle_id

    except MultipleResultsFound as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "MULTIPLES_USUARIOS",
                "message": "Error de integridad: se encontró más de una cuenta para el mismo kc_id.",
            },
        ) from exc


async def decode_and_validate_token(token: str, institute: InstitutesEnum) -> dict:
    """Decodifica y valida firma/claims del token usando las llaves públicas del instituto."""
    jwks = await get_jwks_for_institute(institute)

    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")

    if not kid:
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": "FALTA_KID_TOKEN",
                "message": "Falta 'kid' en el token",
            },
        )

    signing_key = find_signing_key(jwks, kid)
    if not signing_key:
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": "CLAVE_FIRMA_INVALIDA",
                "message": "Clave de firma inválida",
            },
        )

    kc = keycloak_configs[institute]
    issuer = f"{kc.url}/realms/{kc.realm}"

    return jwt.decode(
        token,
        signing_key,
        algorithms=[ALGORITHM],
        audience="account",
        issuer=issuer,
    )


async def get_jwks_for_institute(institute: InstitutesEnum) -> dict:
    """
    Recupera el conjunto de llaves públicas (JWKS) desde el servidor de Keycloak.

    Implementa un mecanismo de caché para evitar peticiones redundantes al
    proveedor de identidad en cada validación de token.
    """
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


def find_signing_key(jwks: dict, kid: str) -> dict | None:
    """
    Busca la clave de firma específica dentro del JWKS utilizando el 'kid'
    (Key ID) presente en el encabezado del token.
    """
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    return None


async def get_moodle_id_from_web_service(
    institute: InstitutesEnum, user_email: str
) -> int:
    """
    Consulta directa al Web Service de Moodle para obtener el ID interno
    a partir del correo electrónico.
    """
    user_profile_result = await MoodleService.get_user_profile_by_email(
        institute=institute, user_email=user_email
    )

    if user_profile_result.error or not user_profile_result.user_profile.get("id"):
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "MOODLE_SYNC_ERROR",
                "message": "Usuario no encontrado en Moodle",
            },
        )

    return user_profile_result.user_profile.get("id")
