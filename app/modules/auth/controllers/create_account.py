# Módulo CreateAccountController - Aprovisionamiento de Servicios Externos
# Coordina la creación de usuarios en Keycloak y Moodle, además de la
# inscripción a cursos, creación de grupos y limpieza de tokens de verificación.

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.auth.services.kc_service import KeycloakService
from app.modules.auth.services.moodle_service import MoodleService
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.enums.role_enum import AccountRoleEnum
from app.shared.enums.status_enum import AccountStatusEnum
from app.shared.models.user_courses_model import UserCourses
from app.shared.models.users_model import UserAccounts
from app.shared.models.verification_tokens_model import VerificationToken

from ..schema import CreateAccountSchema


class CreateAccountController:
    """
    Controlador encargado del flujo de alta definitiva de usuarios.

    Orquesta la integración con:
    - Keycloak: para identidad (IAM)
    - Moodle: para cursos y aprendizaje (LMS)

    Asegura consistencia entre ambos sistemas con rollback en caso de error.
    """

    @staticmethod
    async def create_account(data: CreateAccountSchema, db: Session):
        """
        Realiza el aprovisionamiento completo de una cuenta aprobada.

        Pasos:
        1. Valida que la solicitud exista y esté en estado APPROVED.
        2. Crea el usuario en Keycloak (o recupera su ID si ya existe).
        3. Si es docente y course_id == 0:
           a. Crea UN CURSO POR CADA GRUPO en Moodle.
           b. Inscribe al docente en cada curso creado.
        4. Si es alumno, inscribe al alumno en el curso existente.
        5. Actualiza estados en BD local y elimina tokens temporales.
        """

        # ========== 1. VALIDACIÓN DE LA SOLICITUD ==========
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

        if account_request.status != AccountStatusEnum.APPROVED:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "STATUS_INVALIDO",
                    "message": "La solicitud debe estar aprobada para crear la cuenta",
                },
            )

        # ========== 2. KEYCLOAK - CREACIÓN DE IDENTIDAD ==========
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
            error_msg = str(kc_result.get("error", ""))

            # PARCHE: Si el usuario ya existe en Keycloak, recuperamos su ID
            if (
                "User exists with same username" in error_msg
                or "User exists" in error_msg
            ):
                print(
                    f"⚠️ Usuario {account_request.email} ya existe en Keycloak. Recuperando ID..."
                )

                existing_user = await KeycloakService.get_user_by_email(
                    email=account_request.email, institute=account_request.institute
                )

                if existing_user and existing_user.get("id"):
                    account_request.kc_id = str(existing_user["id"])
                    print(f"✅ ID de Keycloak recuperado: {account_request.kc_id}")
                else:
                    raise HTTPException(
                        status_code=502,
                        detail={
                            "error_code": "KC_ERROR",
                            "message": "Usuario existe en Keycloak pero no se pudo recuperar su ID",
                        },
                    )
            else:
                raise HTTPException(
                    status_code=502,
                    detail={
                        "error_code": "KC_ERROR",
                        "message": f"Error en Keycloak: {kc_result.get('error')}",
                    },
                )
        else:
            # Guardar el UUID de Keycloak como string
            kc_user_id = kc_result.get("user_id")
            if kc_user_id:
                account_request.kc_id = str(kc_user_id)

        # ========== 3. MOODLE - GESTIÓN DE CURSOS ==========
        current_course_id = account_request.course_id
        created_courses = []  # Lista para almacenar los IDs de cursos creados

        # Si es docente y course_id == 0, hay que crear curso(s) NUEVO(s)
        if account_request.role == AccountRoleEnum.DOCENTE and current_course_id == 0:
            # Buscar los detalles del curso solicitado
            course_detail = (
                db.query(UserCourses)
                .filter(
                    UserCourses.auth_id == account_request.id,
                    UserCourses.status == AccountStatusEnum.PENDING,
                )
                .first()
            )

            if course_detail and course_detail.course_full_name:
                # Parsear los grupos (vienen como string "A334,A554")
                groups_str = course_detail.groups or ""
                groups_list = (
                    [g.strip() for g in groups_str.split(",") if g.strip()]
                    if groups_str
                    else ["0"]
                )

                # CREAR UN CURSO POR CADA GRUPO
                for group_name in groups_list:
                    # Generar shortname único para este curso
                    shortname = CreateAccountController._create_course_shortname(
                        institute=account_request.institute,
                        fullname=course_detail.course_full_name,
                        group=group_name,
                    )

                    print(
                        f"🆕 Creando curso: {course_detail.course_full_name} - Grupo: {group_name}"
                    )
                    print(f"   Shortname: {shortname}")

                    # Crear el curso en Moodle
                    moodle_course_res = await MoodleService.create_course(
                        institute=account_request.institute,
                        fullname=course_detail.course_full_name,
                        teacher_name=f"{account_request.name} {account_request.last_name}",
                        shortname=shortname,
                        group_name=group_name,
                    )

                    if moodle_course_res.error:
                        # ROLLBACK: Si falla algún curso, borramos el usuario de Keycloak
                        if account_request.kc_id:
                            await KeycloakService.delete_user(
                                str(account_request.kc_id), account_request.institute
                            )
                        raise HTTPException(
                            status_code=502,
                            detail={
                                "error_code": "COURSE_CREATION_FAILED",
                                "message": f"Error creando curso para grupo {group_name}: {moodle_course_res.error}",
                            },
                        )

                    # Si el curso se creó correctamente, guardamos su ID
                    if moodle_course_res.course and "id" in moodle_course_res.course:
                        course_id = moodle_course_res.course["id"]
                        created_courses.append(course_id)
                        print(
                            f"✅ Curso creado: ID {course_id} - {course_detail.course_full_name} ({group_name})"
                        )

                # Guardar el primer curso como referencia en account_request
                if created_courses:
                    account_request.course_id = created_courses[0]
                    current_course_id = created_courses[0]

                # Marcar el detalle del curso como APPROVED
                course_detail.status = AccountStatusEnum.APPROVED

        # Validación final: debe existir un course_id para continuar
        if current_course_id is None:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "DATA_INCOMPLETE",
                    "message": "ID de curso nulo",
                },
            )

        # ========== 4. MOODLE - CREACIÓN DE USUARIO ==========
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
            # ROLLBACK: Si Moodle falla, borramos el usuario de Keycloak
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
            # ROLLBACK: Fallo controlado en Moodle
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

        # Guardar el ID de Moodle
        account_request.moodle_id = moodle_result.get("id")
        m_user_id = account_request.moodle_id

        # ========== 5. INSCRIPCIÓN AUTOMÁTICA ==========
        if m_user_id is not None:
            if account_request.role == AccountRoleEnum.DOCENTE:
                moodle_role = 3  # editingteacher

                # Inscribir al docente en TODOS los cursos creados
                courses_to_enroll = (
                    created_courses if created_courses else [current_course_id]
                )

                for course_id in courses_to_enroll:
                    await MoodleService.enroll_user(
                        user_id=m_user_id,
                        course_id=course_id,
                        institute=account_request.institute,
                        role_id=moodle_role,
                    )
                    print(f"✅ Docente inscrito en curso {course_id}")
            else:
                moodle_role = 5  # student
                await MoodleService.enroll_user(
                    user_id=m_user_id,
                    course_id=current_course_id,
                    institute=account_request.institute,
                    role_id=moodle_role,
                )

        # Actualizar el registro del curso a APPROVED
        course_record = (
            db.query(UserCourses)
            .filter(
                UserCourses.auth_id == account_request.id,
                UserCourses.status == AccountStatusEnum.PENDING,
            )
            .first()
        )
        if course_record:
            course_record.status = AccountStatusEnum.APPROVED

        # ========== 6. FINALIZACIÓN Y LIMPIEZA ==========
        # Cambiar estado global a CREATED
        account_request.status = AccountStatusEnum.CREATED

        # Eliminar token de verificación (ya fue usado)
        token_record = (
            db.query(VerificationToken)
            .filter(VerificationToken.auth_id == account_request.id)
            .first()
        )
        if token_record:
            db.delete(token_record)

        # Guardar todo en la BD
        db.commit()
        db.refresh(account_request)

        return {
            "message": "Cuenta creada exitosamente",
            "kc_id": account_request.kc_id,
            "moodle_id": account_request.moodle_id,
            "moodle_course_id": current_course_id,
            "created_courses": created_courses
            if created_courses
            else [current_course_id],
        }

    @classmethod
    def _create_course_shortname(
        cls, institute: InstitutesEnum, fullname: str, group: str
    ) -> str:
        """
        Genera el nombre corto oficial (Subject) siguiendo la lógica del proyecto.

        Ejemplo:
            institute = PRINCIPAL
            fullname = "Desarrollo WEB"
            group = "A334"
            Resultado: PRI-DWE-A334
        """
        # Prefijo del instituto: 3 primeras letras en mayúscula
        inst_prefix = str(institute.value)[:3].upper()

        # Iniciales del curso: primera letra de cada palabra (máximo 3)
        words = fullname.split()
        if len(words) >= 2:
            course_initials = "".join([word[0] for word in words[:3]]).upper()
        else:
            course_initials = fullname[:3].upper()

        # Sufijo del grupo
        group_suffix = str(group).upper() if group else "0"

        return f"{inst_prefix}-{course_initials}-{group_suffix}"
