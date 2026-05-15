# Módulo CreateAccountController - Aprovisionamiento de Servicios Externos
# Coordina la creación de usuarios en Keycloak y Moodle, además de la
# inscripción a cursos, creación de grupos y limpieza de tokens de verificación.

from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.register.repositories.create_account_repository import (
    CreateAccountRepository,
)
from app.modules.register.services.kc_service import KeycloakService
from app.modules.register.services.moodle_service import MoodleService
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.enums.role_enum import AccountRoleEnum
from app.shared.enums.status_enum import RequestStatusEnum as AccountStatusEnum
from app.shared.models.auth_model import Auth
from app.shared.models.JIDs_model import JIDs

from ..schemas import CreateAccountSchema


class CreateAccountController:
    """Controlador que orquesta el aprovisionamiento final de una cuenta.

    Separa responsabilidades en funciones privadas para claridad y testabilidad.
    """

    @staticmethod
    async def create_account(data: CreateAccountSchema, db: Session) -> dict[str, Any]:
        """Flujo principal de creación de cuenta.

        Args:
            data: `CreateAccountSchema` con `user_id`, `new_password` y `token`.
            db: Sesión de SQLAlchemy.

        Returns:
            Diccionario con IDs creados y mensaje de éxito.
        """
        repo = CreateAccountRepository(db)

        auth = CreateAccountController._get_auth_or_raise(repo, data.user_id)
        CreateAccountController._validate_verification_tokens(auth)
        CreateAccountController._validate_request_approved(auth)
        if auth.profile is None:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "DATOS_INCOMPLETOS",
                    "message": "El usuario no tiene perfil asociado.",
                },
            )
        profile = auth.profile

        # KEYCLOAK
        CreateAccountController._ensure_jids_record(repo, db, auth)
        await CreateAccountController._create_or_recover_kc(auth, data.new_password)

        # MOODLE - cursos (docente) y creación de usuario
        created_courses: list[int] = []
        current_course_id = CreateAccountController._determine_current_course(auth)

        if profile.role == AccountRoleEnum.DOCENTE:
            created_courses = await CreateAccountController._create_courses_for_teacher(
                repo, auth
            )
            if created_courses:
                current_course_id = created_courses[0]

        if current_course_id is None:
            raise HTTPException(
                status_code=400,
                detail={"error_code": "DATA_INCOMPLETE", "message": "ID de curso nulo"},
            )

        # Crear usuario en Moodle
        moodle_user = await CreateAccountController._create_moodle_user_or_rollback(
            auth, current_course_id
        )

        # Inscripción automática
        if moodle_user and moodle_user.get("id") is not None:
            mid = moodle_user.get("id")
            if mid is not None:
                await CreateAccountController._enroll_user_in_courses(
                    auth, int(mid), created_courses or [current_course_id]
                )

        # Finalizar: actualizar estados y limpiar token
        CreateAccountController._finalize_and_cleanup(repo, db, auth)

        jids = auth.jids
        moodle_id = jids.moodle_id if jids else None

        return {
            "message": "Cuenta creada exitosamente",
            "kc_id": str(jids.kc_id) if jids and jids.kc_id else None,
            "moodle_id": moodle_id,
            "moodle_course_id": current_course_id,
            "created_courses": created_courses
            if created_courses
            else [current_course_id],
        }

    @staticmethod
    def _get_auth_or_raise(repo: CreateAccountRepository, user_id: int) -> Auth:
        """Recupera el `Auth` con relaciones; lanza 404 si no existe."""
        auth = repo.get_auth_with_relations(user_id)
        if auth is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "NO_ENCONTRADO",
                    "message": "Solicitud no encontrada",
                },
            )
        return auth

    @staticmethod
    def _validate_verification_tokens(auth: Auth) -> None:
        """Valida que exista al menos un token de verificación asociado."""
        if not auth.verification_tokens:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "TOKEN_NO_ENCONTRADO",
                    "message": "No se encontró un token de verificación asociado a esta solicitud",
                },
            )

    @staticmethod
    def _validate_request_approved(auth: Auth) -> None:
        """Valida que exista una solicitud de curso aprobada para este usuario."""
        # profile es requerido por el flujo
        if not getattr(auth, "profile", None):
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "DATOS_INCOMPLETOS",
                    "message": "El usuario no tiene perfil asociado.",
                },
            )
        approved = False

        for req in getattr(auth, "student_course_requests", []) or []:
            if req.status == AccountStatusEnum.APPROVED:
                approved = True
                break

        if not approved:
            for req in getattr(auth, "teacher_course_requests", []) or []:
                if req.status == AccountStatusEnum.APPROVED:
                    approved = True
                    break

        if not approved:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "STATUS_INVALIDO",
                    "message": "La solicitud debe estar aprobada para crear la cuenta",
                },
            )

    @staticmethod
    def _ensure_jids_record(
        repo: CreateAccountRepository, db: Session, auth: Auth
    ) -> JIDs:
        """Asegura que exista `JIDs` y lo persiste en la sesión si hace falta."""
        jid = repo.ensure_jids(auth)
        # Guardar el nuevo JIDs temporal en la sesión para que pueda usarse
        db.flush()
        return jid

    @staticmethod
    async def _create_or_recover_kc(auth: Auth, password: str) -> None:
        """Crea el usuario en Keycloak o recupera su ID si ya existe.

        Divide la lógica para reducir complejidad cognitiva.
        """
        profile = auth.profile
        if profile is None:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "DATOS_INCOMPLETOS",
                    "message": "El usuario no tiene perfil asociado.",
                },
            )

        kc_result = await KeycloakService.create_user(
            {
                "name": profile.name,
                "last_name": profile.last_name,
                "email": auth.email,
                "password": password,
            },
            institute=auth.institute,
        )

        created = None
        # Soporta dict-like o objeto con atributos
        if isinstance(kc_result, dict):
            created = kc_result.get("created")
        else:
            created = getattr(kc_result, "created", None)

        if created:
            user_id = (
                kc_result.get("user_id")
                if isinstance(kc_result, dict)
                else getattr(kc_result, "user_id", None)
            )
            if user_id:
                CreateAccountController._store_kc_id_in_jids(auth, user_id)
            return

        # No creado: intentar recuperar por email
        error_msg = (
            str(kc_result.get("error", ""))
            if isinstance(kc_result, dict)
            else str(getattr(kc_result, "error", ""))
        )
        if "User exists" in error_msg or "User exists with same username" in error_msg:
            await CreateAccountController._recover_existing_kc(auth)
        else:
            raise HTTPException(
                status_code=502,
                detail={
                    "error_code": "KC_ERROR",
                    "message": f"Error en Keycloak: {error_msg}",
                },
            )

    @staticmethod
    async def _recover_existing_kc(auth: Auth) -> None:
        existing_user = await KeycloakService.get_user_by_email(
            email=auth.email, institute=auth.institute
        )
        if existing_user and existing_user.get("id"):
            CreateAccountController._store_kc_id_in_jids(auth, existing_user["id"])
        else:
            raise HTTPException(
                status_code=502,
                detail={
                    "error_code": "KC_ERROR",
                    "message": "Usuario existe en Keycloak pero no se pudo recuperar su ID",
                },
            )

    @staticmethod
    def _store_kc_id_in_jids(auth: Auth, kc_id_value: Any) -> None:
        """Almacena `kc_id` en `auth.jids`, intentando convertir a UUID cuando sea posible."""
        if not auth.jids:
            raise HTTPException(
                status_code=502,
                detail={
                    "error_code": "KC_ERROR",
                    "message": "No existe registro de JIDs para guardar kc_id",
                },
            )
        try:
            auth.jids.kc_id = UUID(str(kc_id_value))
        except Exception:
            # Si no es convertible, guárdalo tal cual (compatibilidad)
            auth.jids.kc_id = kc_id_value

    @staticmethod
    def _determine_current_course(auth: Auth) -> int | None:
        """Determina el `course_id` actual a usar para la creación e inscripción."""
        # Prioriza cualquier moodle_course_id en solicitudes de alumno
        for s in getattr(auth, "student_course_requests", []) or []:
            if s.moodle_course_id:
                return s.moodle_course_id

        # Si es docente, puede no existir aún (se crearán cursos más adelante)
        return None

    @staticmethod
    async def _create_courses_for_teacher(
        repo: CreateAccountRepository, auth: Auth
    ) -> list[int]:
        """Crea en Moodle los cursos requeridos por una solicitud de docente.

        Retorna la lista de course IDs creados.
        """
        created_courses: list[int] = []
        course_detail = repo.get_pending_teacher_course(auth.id)
        if not course_detail or not course_detail.course_full_name:
            return created_courses

        groups_str = course_detail.groups or ""
        groups_list = (
            [g.strip() for g in groups_str.split(",") if g.strip()]
            if groups_str
            else ["0"]
        )

        # Crear todos los cursos en una sola llamada al servicio de Moodle
        profile = auth.profile
        if profile is None:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "DATOS_INCOMPLETOS",
                    "message": "El usuario no tiene perfil asociado.",
                },
            )

        # Llamada única al servicio para crear múltiples cursos
        create_res = await MoodleService.create_courses(
            institute=auth.institute,
            fullname=course_detail.course_full_name,
            groups=groups_list,
        )

        if getattr(create_res, "error", None):
            raise HTTPException(
                status_code=502,
                detail={
                    "error_code": "COURSE_CREATION_FAILED",
                    "message": f"Error creando cursos: {create_res.error}",
                },
            )

        # El servicio retorna `course_ids`.
        created_courses = getattr(create_res, "course_ids", []) or []

        # Marcar el detalle del curso como APPROVED localmente
        course_detail.status = AccountStatusEnum.APPROVED

        return created_courses

    @staticmethod
    async def _create_moodle_user_or_rollback(
        auth: Auth, course_id: int
    ) -> dict[str, Any]:
        """Crea el usuario en Moodle; lanza y permite rollback si falla."""
        try:
            profile = auth.profile
            if profile is None:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error_code": "DATOS_INCOMPLETOS",
                        "message": "El usuario no tiene perfil asociado.",
                    },
                )

            moodle_result = await MoodleService.create_user(
                user_data={
                    "name": profile.name,
                    "last_name": profile.last_name,
                    "email": auth.email,
                    "course_id": course_id,
                },
                institute=auth.institute,
            )
        except Exception as e:
            # No manejamos borrado de Keycloak aquí; llamador ya tiene el registro
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "MOODLE_CONNECTION_ERROR",
                    "message": f"No se pudo conectar con Moodle: {str(e)}",
                },
            ) from e

        # Extraer el flag `created` soportando dict-like y objeto
        created_flag = None
        if isinstance(moodle_result, dict):
            created_flag = moodle_result.get("created")
        else:
            created_flag = getattr(moodle_result, "created", None)

        if not created_flag:
            raise HTTPException(
                status_code=502,
                detail={
                    "error_code": "MOODLE_ERROR",
                    "message": "Error al crear usuario en Moodle",
                },
            )

        # Guardar moodle id en JIDs
        if not auth.jids:
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "JIDS_MISSING",
                    "message": "Registro de JIDs no encontrado para almacenar moodle_id",
                },
            )
        moodle_id = (
            moodle_result.get("id")
            if isinstance(moodle_result, dict)
            else getattr(moodle_result, "id", None)
        )
        auth.jids.moodle_id = moodle_id
        # retornar un mapping para el llamador
        return {"created": True, "id": moodle_id}

    @staticmethod
    async def _enroll_user_in_courses(
        auth: Auth, moodle_user_id: int, course_ids: list[int]
    ) -> None:
        """Inscribe el usuario en los cursos indicados según su rol."""
        profile = auth.profile
        if profile is None:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "DATOS_INCOMPLETOS",
                    "message": "El usuario no tiene perfil asociado.",
                },
            )

        moodle_role = 3 if profile.role == AccountRoleEnum.DOCENTE else 5

        for cid in course_ids:
            await MoodleService.enroll_user(
                user_id=moodle_user_id,
                course_id=cid,
                institute=auth.institute,
                role_id=moodle_role,
            )

    @staticmethod
    def _finalize_and_cleanup(
        repo: CreateAccountRepository, db: Session, auth: Auth
    ) -> None:
        """Actualiza estados locales, elimina tokens y persiste la transacción."""
        # Actualizar solicitudes pendientes relacionadas a APPROVED
        for rec in getattr(auth, "student_course_requests", []) or []:
            if rec.status == AccountStatusEnum.PENDING:
                rec.status = AccountStatusEnum.APPROVED

        for rec in getattr(auth, "teacher_course_requests", []) or []:
            if rec.status == AccountStatusEnum.PENDING:
                rec.status = AccountStatusEnum.APPROVED

        # No existe campo `status` en Auth; en design original habría uno.
        # Se asume que el acto de creación marca la solicitud como ENROLLED/CREATED

        # Eliminar token
        repo.delete_verification_token(auth.id)

        # Persistir
        db.commit()
        db.refresh(auth)

    @classmethod
    def _create_course_shortname(
        cls, institute: InstitutesEnum, fullname: str, group: str
    ) -> str:
        """Genera shortname de curso (prefijo-iniciales-grupo)."""
        inst_prefix = str(institute.value)[:3].upper()
        words = fullname.split()
        if len(words) >= 2:
            course_initials = "".join([word[0] for word in words[:3]]).upper()
        else:
            course_initials = fullname[:3].upper()
        group_suffix = str(group).upper() if group else "0"
        return f"{inst_prefix}-{course_initials}-{group_suffix}"
