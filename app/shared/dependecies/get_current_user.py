"""
Dependencia para obtener el usuario autenticado a partir de la información del token Bearer.
"""

from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.shared.dependecies.auth_verify import BearerUserInfo, validate_jwt_token
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.enums.role_enum import AccountRoleEnum
from app.shared.models.auth_model import Auth
from app.shared.models.JIDs_model import JIDs
from app.shared.models.user_profiles_model import UserProfile
from app.shared.services.moodle_service import MoodleService


@dataclass
class AuthenticationIds:
    """Estructura de resultado para la consulta de IDs."""

    moodle_id: int
    auth_id: int


class IdentityRepository:
    """Encapsula el acceso de datos de identidad para mantener consultas legibles."""

    def __init__(self, db: Session):
        self.db = db

    def get_ids_by_kc_id(self, kc_id: UUID) -> AuthenticationIds | None:
        """Retorna el moodle_id y auth_id vinculados al kc_id o None si no existe relación."""
        stmt = select(JIDs.moodle_id, JIDs.auth_id).where(JIDs.kc_id == kc_id)
        result = self.db.execute(stmt).one_or_none()

        if result is None:
            return None

        return AuthenticationIds(moodle_id=result.moodle_id, auth_id=result.auth_id)

    def create_identity(
        self, user_info: BearerUserInfo, institute: InstitutesEnum, moodle_id: int
    ) -> int:
        """Crea identidad local completa (Auth + Profile + JIDs) para usuario sincronizado."""
        # TODO: Cachear errores
        auth = Auth(email=user_info.email, institute=institute)
        profile = UserProfile(
            name=user_info.name,
            last_name=user_info.last_name,
            role=AccountRoleEnum.ALUMNO,
        )
        jids = JIDs(kc_id=user_info.kc_id, moodle_id=moodle_id)

        auth.profile = profile
        auth.jids = jids

        self.db.add(auth)
        self.db.commit()
        self.db.refresh(auth)
        return auth.id


class CurrentUser(BearerUserInfo):
    """Extensión del modelo de usuario con IDs internos de MACTI y Moodle."""

    moodle_id: int = Field(..., description="ID del usuario en Moodle")
    auth_id: int = Field(
        ..., description="ID interno del usuario en la tabla de autenticación"
    )


async def get_current_user(
    institute: InstitutesEnum,
    db: Session = Depends(get_db),
    bearer_user_info: BearerUserInfo = Depends(validate_jwt_token),
) -> CurrentUser:
    """
    Dependencia de FastAPI que valida el token Bearer y retorna el usuario autenticado.

    Proceso:
    1. Valida el token JWT y extrae la información del usuario (BearerUserInfo).
    2. Consulta la base de datos para encontrar los IDs internos (moodle_id, auth_id) asociados al kc_id del usuario.
    3. Si no se encuentra una relación, realiza una sincronización automática con Moodle para obtener el moodle_id y crear el registro local.
    4. Retorna un objeto CurrentUser con toda la información unificada.
    """
    repository = IdentityRepository(db)

    ids_result = repository.get_ids_by_kc_id(bearer_user_info.kc_id)
    if ids_result is not None:
        return CurrentUser(
            moodle_id=ids_result.moodle_id,
            auth_id=ids_result.auth_id,
            **bearer_user_info.model_dump(),
        )

    auth_ids = await sync_user(bearer_user_info, repository, institute)

    return CurrentUser(
        moodle_id=auth_ids.moodle_id,
        auth_id=auth_ids.auth_id,
        **bearer_user_info.model_dump(),
    )


async def sync_user(
    user_info: BearerUserInfo, repository: IdentityRepository, institute: InstitutesEnum
) -> AuthenticationIds:
    """
    Sincroniza el usuario con Moodle y crea la identidad local si no existe relación previa.
    """
    moodle_id = await get_moodle_id_from_web_service(institute, user_info.email)
    auth_id = repository.create_identity(
        user_info=user_info, institute=institute, moodle_id=moodle_id
    )
    return AuthenticationIds(moodle_id=moodle_id, auth_id=auth_id)


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
