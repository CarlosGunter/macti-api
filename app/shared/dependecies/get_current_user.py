from uuid import UUID

import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError, JWTError
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.models import AccountRequest
from app.shared.config.kc_configs import keycloak_configs
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.services.moodle_service import MoodleService

security = HTTPBearer()
ALGORITHM = "RS256"

JWKS_CACHE: dict[InstitutesEnum, dict] = {}


async def get_jwks_for_institute(institute: InstitutesEnum) -> dict:
    if institute not in JWKS_CACHE:
        print(f"[DEBUG] JWKS para {institute.value} NO está en cache. Obteniendo...")

        kc = keycloak_configs[institute]
        url = f"{kc.url}/realms/{kc.realm}/protocol/openid-connect/certs"

        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            print(f"[DEBUG] GET {url} -> status {resp.status_code}")

            if resp.status_code != 200:
                print("[ERROR] No se pudieron obtener JWKS:", resp.text)
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error_code": "KC_JWKS_ERROR",
                        "message": f"No se pudieron obtener JWKS para {institute.value}",
                    },
                )

            JWKS_CACHE[institute] = resp.json()
            print(f"[DEBUG] JWKS guardado en cache para {institute.value}")

    else:
        print(f"[DEBUG] JWKS para {institute.value} tomado de cache")

    return JWKS_CACHE[institute]


def find_signing_key(jwks: dict, kid: str) -> dict | None:
    print(f"[DEBUG] Buscando 'kid' {kid} dentro de JWKS...")

    for key in jwks.get("keys", []):
        print(f"[DEBUG] Revisando key con kid={key.get('kid')}")
        if key.get("kid") == kid:
            print("[DEBUG] Clave encontrada ✔")
            return key

    print("[ERROR] No se encontró la clave con ese kid ")
    return None


class CurrentUser(BaseModel):
    kc_id: UUID = Field(..., alias="sub")
    email: str = Field(..., alias="email")
    name: str = Field(..., alias="given_name")
    last_name: str = Field(..., alias="family_name")


class CurrentUserReturn(CurrentUser):
    moodle_id: int


async def get_current_user(
    institute: InstitutesEnum,
    db: Session = Depends(get_db),
    credentials=Depends(security),
) -> CurrentUserReturn:
    token = credentials.credentials
    jwks = await get_jwks_for_institute(institute)
    try:
        unverified_header = jwt.get_unverified_header(token)

        kid = unverified_header.get("kid")

        if not kid:
            raise HTTPException(
                status_code=401,
                detail={
                    "error_code": "FALTA_KID_TOKEN",
                    "message": "Falta 'kid' en el encabezado del token",
                },
            )

    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": "ENCABEZADO_TOKEN_INVALIDO",
                "message": "Encabezado del token inválido",
            },
        ) from e

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

    try:
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=[ALGORITHM],
            audience="account",
            issuer=issuer,
        )

        azp = payload.get("azp")

        if azp != "next-login":
            raise HTTPException(
                status_code=401,
                detail={
                    "error_code": "CLIENTE_INVALIDO",
                    "message": "Cliente (azp) inválido en el token",
                },
            )

        user_kc_parsed = CurrentUser(**payload)
        moodle_id = await get_user_moodle_id(user_kc_parsed, db, institute)

        alias_data = user_kc_parsed.model_dump(by_alias=True)
        alias_data["moodle_id"] = moodle_id
        user_parsed: CurrentUserReturn = CurrentUserReturn.model_validate(alias_data)

        return user_parsed

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail={"error_code": "TOKEN_EXPIRADO", "message": "Token expirado"},
        ) from ExpiredSignatureError

    except JWTClaimsError:
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": "RECLAMACIONES_TOKEN_INVALIDAS",
                "message": "Reclamaciones del token inválidas",
            },
        ) from JWTClaimsError

    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail={"error_code": "FIRMA_TOKEN_INVALIDA", "message": "Token inválido"},
        ) from e

    except ValidationError as e:
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": "VALIDACION_FALLIDA",
                "message": "Respuesta de información de usuario inválida",
            },
        ) from e


async def get_user_moodle_id(
    user_info: CurrentUser, db: Session, institute: InstitutesEnum
) -> int:
    """
    Obtiene el ID de Moodle del usuario a partir de la información del token.

    Verifica en la base de datos u obtiene desde Moodle si es necesario.
    """
    kc_id = user_info.kc_id
    user_email = user_info.email

    try:
        query = db.query(AccountRequest).filter(AccountRequest.kc_id == kc_id).one()
        if not query.moodle_id:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "MOODLE_NO_ENCONTRADO",
                    "message": "El usuario no tiene un ID de Moodle asociado.",
                },
            )
        return query.moodle_id

    except NoResultFound:
        moodle_id = await get_moodle_id_from_web_service(
            institute=institute, user_email=user_email
        )

        sync_user = AccountRequest(
            email=user_email,
            name=user_info.name,
            last_name=user_info.last_name,
            institute=institute,
            moodle_id=moodle_id,
            kc_id=kc_id,
        )
        db.add(sync_user)
        db.commit()
        db.refresh(sync_user)

        return moodle_id

    except MultipleResultsFound:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "MULTIPLES_RESULTADOS",
                "message": "Múltiples usuarios encontrados, error interno.",
            },
        ) from MultipleResultsFound


async def get_moodle_id_from_web_service(
    institute: InstitutesEnum, user_email: str
) -> int:
    """
    Sincroniza la información del usuario en la base de datos local
    obteniendo su ID de Moodle desde el servicio de Moodle.
    """
    user_profile_result = await MoodleService.get_user_profile_by_email(
        institute=institute, user_email=user_email
    )

    if user_profile_result.error:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "MOODLE_SYNC_ERROR",
                "message": f"Error al obtener perfil de usuario desde Moodle: {user_profile_result.error}",
            },
        )

    user_moodle_id = user_profile_result.user_profile.get("id")

    if not user_moodle_id:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "MOODLE_USER_NOT_FOUND",
                "message": f"Usuario con email {user_email} no encontrado en Moodle.",
            },
        )

    return user_moodle_id
