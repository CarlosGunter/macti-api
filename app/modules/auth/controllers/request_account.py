# Módulo RequestAccountController - Captura y Validación de Solicitudes
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
        """
        if role == AccountRoleEnum.DOCENTE and isinstance(data, TeacherRequestSchema):
            RequestAccountController._print_teacher_subject_request(data)

        # 1. Verificar si ya existe una solicitud para este correo e instituto
        existing_request = (
            db.query(UserAccounts)
            .filter(
                UserAccounts.email == data.email,
                UserAccounts.institute == data.institute,
            )
            .first()
        )

        if existing_request is not None:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "EMAIL_EXISTENTE",
                    "message": "El correo ya tiene una solicitud registrada en este instituto.",
                },
            )

        try:
            # 2. Crear el registro base de la cuenta
            db_account_request = UserAccounts(
                name=data.name,
                last_name=data.last_name,
                email=data.email,
                institute=data.institute,
                role=role,
                status=AccountStatusEnum.PENDING,
                course_id=data.course_id,
            )

            db.add(db_account_request)
            db.flush()

            # 3. Registro de detalles adicionales si es docente
            if role == AccountRoleEnum.DOCENTE and isinstance(
                data, TeacherRequestSchema
            ):
                course_name = data.course_full_name
                group_info = data.groups

                detalles_curso = UserCourses(
                    user_id=db_account_request.id,
                    course_full_name=course_name,
                    groups=group_info,
                    status=AccountStatusEnum.PENDING,
                )
                db.add(detalles_curso)

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

    @staticmethod
    def _print_teacher_subject_request(data: TeacherRequestSchema):
        """
        Genera una representación visual en consola del curso solicitado.
        """
        try:
            inst_prefix = str(data.institute.value)[:3].upper()

            words = data.course_full_name.split()
            if len(words) >= 2:
                course_initials = "".join([word[0] for word in words[:3]]).upper()
            else:
                course_initials = data.course_full_name[:3].upper()

            group = str(data.groups).upper() if data.groups else "0"
            subject_code = f"{inst_prefix}-{course_initials}-{group}"

            print("\n" + "═" * 60)
            print("SOLICITUD DE CREACIÓN DE ESPACIO (DOCENTE)")
            print(f"CÓDIGO GENERADO (SUBJECT): {subject_code}")
            print(f"CURSO SOLICITADO: {data.course_full_name}")
            print(f"INSTITUTO: {data.institute.value}")
            print("═" * 60 + "\n")

        except Exception as e:
            print(f"DEBUG LOG: Error al generar el preview del subject: {e}")
