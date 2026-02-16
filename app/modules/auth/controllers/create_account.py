# Módulo CreateAccountController - Aprovisionamiento de Servicios Externos
# Coordina la creación de usuarios en Keycloak y Moodle, además de la
# inscripción a cursos y la limpieza de tokens de verificación.

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.auth.services.kc_service import KeycloakService
from app.modules.auth.services.moodle_service import MoodleService
from app.shared.enums.role_enum import AccountRoleEnum
from app.shared.enums.status_enum import AccountStatusEnum
from app.shared.models.user_courses_model import UserCourses
from app.shared.models.users_model import UserAccounts
from app.shared.models.verification_tokens_model import VerificationToken

from ..schema import CreateAccountSchema


class CreateAccountController:
    """
    Controlador encargado del flujo de alta definitiva de usuarios.

    Orquesta la integración con Keycloak para identidad y Moodle para
    el aprendizaje, asegurando consistencia entre ambos sistemas.
    """

    @staticmethod
    def _generate_moodle_shortname(
        institute_val: str, course_name: str, group: str | None
    ) -> str:
        """
        Genera el nombre corto compuesto: PREFIJOINST-PREFIJOCURSO-GRUPO
        """
        inst_prefix = str(institute_val)[:3].upper()
        words = course_name.split()
        if len(words) >= 2:
            course_initials = "".join([word[0] for word in words[:3]]).upper()
        else:
            course_initials = course_name[:3].upper()

        group_suffix = str(group).upper() if group and group != "None" else "0"
        return f"{inst_prefix}-{course_initials}-{group_suffix}"

    @staticmethod
    async def create_account(data: CreateAccountSchema, db: Session):
        """
        Realiza el aprovisionamiento completo de una cuenta aprobada.

        Pasos:
        1. Valida que la solicitud exista y esté aprobada.
        2. Crea el usuario en Keycloak.
        3. Crea el curso en Moodle (si el ID es 0).
        4. Crea el usuario en Moodle (con rollback de Keycloak si falla).
        5. Inscribe al usuario en el curso correspondiente con rol dinámico.
        6. Actualiza estados en BD local y elimina tokens temporales.
        """

        # 1. Validación de la solicitud
        account_request = (
            db.query(UserAccounts).filter(UserAccounts.id == data.user_id).first()
        )

        if not account_request:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "NO_ENCONTRADO",
                    "message": "Solicitud no encontrada",
                },
            )

        # Validación de estatus previo necesario
        if account_request.status != AccountStatusEnum.APPROVED:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "STATUS_INVALIDO",
                    "message": "La solicitud debe estar aprobada para crear la cuenta",
                },
            )

        # 2. Keycloak (Aprovisionamiento de Identidad)
        kc_result = await KeycloakService.create_user(
            {
                "name": account_request.name,
                "last_name": account_request.last_name,
                "email": account_request.email,
                "password": data.new_password,
            },
            institute=account_request.institute,
        )

        if not kc_result.get("created"):
            raise HTTPException(
                status_code=502,
                detail={
                    "error_code": "KC_ERROR",
                    "message": f"Error en Keycloak: {kc_result.get('error')}",
                },
            )

        # Asignación segura del UUID de Keycloak
        kc_user_id = kc_result.get("user_id")
        if kc_user_id:
            account_request.kc_id = UUID(str(kc_user_id))

        # 3. Moodle - Gestión de Curso y Usuario
        current_course_id = account_request.course_id

        # LÓGICA DE CREACIÓN: Si el docente solicita curso (ID 0), lo creamos primero
        if account_request.role == AccountRoleEnum.DOCENTE and current_course_id == 0:
            course_detail = (
                db.query(UserCourses)
                .filter(UserCourses.user_id == account_request.id)
                .first()
            )

            # Validamos que existan los detalles y el nombre no sea nulo para Pyright
            if course_detail and course_detail.course_full_name:
                # Generamos el nombre corto compuesto solicitado (INST-CUR-GRP)
                composed_shortname = CreateAccountController._generate_moodle_shortname(
                    institute_val=account_request.institute.value,
                    course_name=course_detail.course_full_name,
                    group=course_detail.groups,
                )

                # Invocamos la creación en Moodle enviando el shortname generado
                # Usamos type: ignore porque Pyright tiene un problema detectando el método estático
                moodle_course_res = await MoodleService.create_course(  # type: ignore
                    institute=account_request.institute,
                    fullname=course_detail.course_full_name,
                    shortname=composed_shortname,
                    teacher_name=f"{account_request.name} {account_request.last_name}",
                    group_name=course_detail.groups or "0",
                )

                if moodle_course_res.error:
                    # Rollback Keycloak si no se pudo crear el curso
                    if account_request.kc_id:
                        await KeycloakService.delete_user(
                            str(account_request.kc_id), account_request.institute
                        )
                    raise HTTPException(
                        status_code=502,
                        detail={
                            "error_code": "COURSE_CREATION_FAILED",
                            "message": moodle_course_res.error,
                        },
                    )

                # Actualizamos el ID local con el ID real de Moodle (ej. 105)
                if moodle_course_res.course and "id" in moodle_course_res.course:
                    current_course_id = moodle_course_res.course["id"]
                    account_request.course_id = current_course_id

        if current_course_id is None:
            raise HTTPException(
                status_code=400,
                detail={"error_code": "DATA_INCOMPLETE", "message": "ID de curso nulo"},
            )

        # 4. Moodle - Aprovisionamiento de usuario
        try:
            moodle_result = await MoodleService.create_user(
                user_data={
                    "name": account_request.name,
                    "last_name": account_request.last_name,
                    "email": account_request.email,
                    "course_id": current_course_id,
                },
                institute=account_request.institute,
            )
        except Exception as e:
            # ROLLBACK: Si Moodle falla, borramos el rastro en Keycloak
            if account_request.kc_id:
                await KeycloakService.delete_user(
                    user_id=str(account_request.kc_id),
                    institute=account_request.institute,
                )
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "MOODLE_CONNECTION_ERROR",
                    "message": f"No se pudo conectar con Moodle: {str(e)}",
                },
            ) from e

        if not moodle_result.get("created"):
            # ROLLBACK: Fallo controlado en la lógica de Moodle
            if account_request.kc_id:
                await KeycloakService.delete_user(
                    user_id=str(account_request.kc_id),
                    institute=account_request.institute,
                )
            raise HTTPException(
                status_code=502,
                detail={
                    "error_code": "MOODLE_ERROR",
                    "message": "Error al crear usuario en Moodle",
                },
            )

        account_request.moodle_id = moodle_result.get("id")
        m_user_id = account_request.moodle_id

        # 5. Inscripción Automática con Roles (Docente: 3, Alumno: 5)
        if m_user_id is not None:
            moodle_role = 3 if account_request.role == AccountRoleEnum.DOCENTE else 5
            await MoodleService.enroll_user(
                user_id=m_user_id,
                course_id=current_course_id,
                institute=account_request.institute,
                role_id=moodle_role,
            )

        # Actualizamos el registro del curso del usuario a APPROVED
        course_record = (
            db.query(UserCourses)
            .filter(
                UserCourses.user_id == account_request.id,
                UserCourses.status == AccountStatusEnum.PENDING,
            )
            .first()
        )
        if course_record:
            course_record.status = AccountStatusEnum.APPROVED

        # 6. Finalización y Limpieza
        # Cambiamos el estatus global a CREATED
        account_request.status = AccountStatusEnum.CREATED

        token_record = (
            db.query(VerificationToken)
            .filter(VerificationToken.account_id == account_request.id)
            .first()
        )
        if token_record:
            db.delete(token_record)

        db.commit()
        db.refresh(account_request)

        return {
            "message": "Cuenta creada exitosamente",
            "kc_id": str(account_request.kc_id),
            "moodle_id": account_request.moodle_id,
            "moodle_course_id": current_course_id,
        }
