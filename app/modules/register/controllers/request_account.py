# Módulo RequestAccountController - Captura y Validación de Solicitudes
#
# Este controlador es la puerta de entrada para los nuevos usuarios en el sistema.
# Maneja la lógica inicial de registro para Alumnos y Docentes, validando duplicados
# y generando códigos de identificación interna (Subjects) para personal académico.

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.shared.enums.role_enum import AccountRoleEnum
from app.shared.enums.status_enum import AccountStatusEnum
from app.shared.models.user_courses_model import UserCourses
from app.shared.models.users_model import UserAccounts

from ..schema import StudentRequestSchema, TeacherRequestSchema


class RequestAccountController:
    """
    Controlador encargado de procesar las peticiones iniciales de registro de cuenta.
    Incluye lógica de validación de correo único por instituto y generación de logs.
    """

    @staticmethod
    def request_account(
        role: AccountRoleEnum,
        data: StudentRequestSchema | TeacherRequestSchema,
        db: Session,
    ):
        """
        Punto de entrada principal para registrar una solicitud de cuenta.

        Args:
            role: ALUMNO o DOCENTE
            data: Datos de la solicitud (varía según el rol)
            db: Sesión de base de datos

        Returns:
            dict: Mensaje de éxito
        """

        # 1. Verificar si ya existe una solicitud para este correo e instituto
        existing_request = (
            db.query(UserAccounts)
            .filter(
                UserAccounts.email == data.email,
                UserAccounts.institute == data.institute,
            )
            .one_or_none()
        )

        if existing_request is None:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "EMAIL_EXISTENTE",
                    "message": "El correo ya tiene una solicitud registrada en este instituto.",
                },
            )

        if existing_request.status == AccountStatusEnum.REJECTED:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "SOLICITUD_RECHAZADA",
                    "message": "Tu solicitud anterior fue rechazada. Por favor, contacta al administrador para más información.",
                },
            )

        try:
            # Si course_id es None, lo ponemos como 0 (indica creación de curso nuevo)
            course_id_value = data.course_id if data.course_id else 0

            # 2. Crear el registro base de la cuenta en MCT_auth
            db_account_request = UserAccounts(
                name=data.name,
                last_name=data.last_name,
                email=data.email,
                institute=data.institute,
                role=role,
                status=AccountStatusEnum.PENDING,
                course_id=course_id_value,
            )

            db.add(db_account_request)
            db.flush()  # Para obtener el ID generado sin hacer commit

            # 3. Si es docente, guardar detalles del curso en MCT_user_courses
            if role == AccountRoleEnum.DOCENTE and isinstance(
                data, TeacherRequestSchema
            ):
                group_info = data.groups
                # Guardamos los grupos como string separado por comas: "G1,G2,G3"
                grupos_str = ",".join(group_info) if group_info else None

                detalles_curso = UserCourses(
                    auth_id=db_account_request.id,  # FK al usuario recién creado
                    course_full_name=data.course_full_name,
                    groups=grupos_str,
                    status=AccountStatusEnum.PENDING,
                )
                db.add(detalles_curso)

            # 4. Confirmar todo en la base de datos
            db.commit()
            db.refresh(db_account_request)

            return {"message": "Solicitud de cuenta procesada exitosamente"}

        except SQLAlchemyError as e:
            db.rollback()
            print(f"DATABASE ERROR: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "DB_ERROR",
                    "message": "Error interno al registrar la solicitud en la base de datos",
                },
            ) from None

        except Exception as e:
            db.rollback()
            print(f"CRITICAL ERROR: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "ERROR_DESCONOCIDO",
                    "message": "Ocurrió un error inesperado en el servidor",
                },
            ) from None
