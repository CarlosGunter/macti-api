"""
Módulo RequestAccountController - Captura y Validación de Solicitudes

Este controlador es la puerta de entrada para los nuevos usuarios en el sistema.
Maneja la lógica inicial de registro para Alumnos y Docentes, validando que no
existan solicitudes duplicadas y generando códigos de identificación interna
(Subjects) para los cursos solicitados por el personal académico.
"""

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.shared.enums.role_enum import AccountRoleEnum
from app.shared.models.user_courses_model import UserCourses
from app.shared.models.users_model import UserAccounts

from ....shared.models.users_model import AccountStatusEnum
from ..schema import StudentRequestSchema, TeacherRequestSchema


class RequestAccountController:
    """
    Controlador encargado de procesar las peticiones iniciales de registro de cuenta.
    Incluye lógica de validación de correo único por instituto y generación de logs
    para el seguimiento de solicitudes académicas.
    """

    @staticmethod
    def request_account(
        role: AccountRoleEnum,
        data: StudentRequestSchema | TeacherRequestSchema,
        db: Session,
    ):
        """
        Punto de entrada principal para registrar una solicitud de cuenta.

        Flujo de ejecución:
        1. Si es Docente, genera un preview del código de curso en logs.
        2. Verifica que el email no tenga una solicitud activa en el mismo instituto.
        3. Persiste la información en la tabla UserAccounts con estatus PENDING.
        """

        # Lógica visual para seguimiento en consola si es una solicitud académica
        if role == AccountRoleEnum.DOCENTE:
            RequestAccountController._print_teacher_subject_request(data)

        # Validación de duplicidad: Un correo no puede pedir dos cuentas en el mismo instituto
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
            """
            Creación del registro de cuenta. 
            Se utiliza getattr para manejar de forma segura los campos que solo
            vienen en la solicitud de Docente (course_full_name, course_key, groups).
            """
            db_account_request = UserAccounts(
                name=data.name,
                last_name=data.last_name,
                email=data.email,
                institute=data.institute,
                role=role,
                status=AccountStatusEnum.PENDING,
                course_id=data.course_id,
            )
            detalles_curso = UserCourses(
                course_full_name=data.course_full_name,
                groups=data.groups,
                status=AccountStatusEnum.PENDING,
            )

            db_account_request.assigned_courses.append(detalles_curso)
            db.add(db_account_request)
            db.commit()
            db.refresh(db_account_request)

            return {"message": "Solicitud de cuenta procesada exitosamente"}

        except SQLAlchemyError:
            """Manejo de errores a nivel de capa de persistencia."""
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "DB_ERROR",
                    "message": "Error interno al registrar la solicitud en la base de datos",
                },
            ) from None

        except Exception as e:
            """Captura de errores críticos no previstos."""
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
        Método de soporte para depuración (Logging).

        Genera una representación visual en consola del curso que se está intentando
        solicitar, creando un código 'Subject' basado en el instituto y las iniciales.
        Formato: [INST_PREFIJO]-[INICIALES_CURSO]-[GRUPO]
        """
        try:
            # Prefijo del instituto (Ej: ING para Ingeniería)
            inst_prefix = str(data.institute.value)[:3].upper()

            # Generación de iniciales del nombre del curso
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
