from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.shared.enums.role_enum import AccountRoleEnum

from ....shared.models.users_model import AccountStatusEnum, UserAccounts
from ..schema import StudentRequestSchema, TeacherRequestSchema


class RequestAccountController:
    @staticmethod
    def _print_teacher_subject_request(data: TeacherRequestSchema):
        """
        Genera e imprime en consola el código de curso (Subject)
        que el docente está solicitando crear.
        Formato: [INSTITUTO]-[INICIALES CURSO]-[GRUPO]
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
            print(f"ÓDIGO GENERADO (SUBJECT): {subject_code}")
            print(f"CURSO SOLICITADO: {data.course_full_name}")
            print(f"INSTITUTO: {data.institute.value}")
            print("═" * 60 + "\n")

        except Exception as e:
            print(f"DEBUG LOG: Error al generar el preview del subject: {e}")

    @staticmethod
    def request_account(
        role: AccountRoleEnum,
        data: StudentRequestSchema | TeacherRequestSchema,
        db: Session,
    ):
        if role == AccountRoleEnum.DOCENTE:
            RequestAccountController._print_teacher_subject_request(data)
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
            db_account_request = UserAccounts(
                name=data.name,
                last_name=data.last_name,
                email=data.email,
                course_id=data.course_id,
                institute=data.institute,
                role=role,
                status=AccountStatusEnum.PENDING,
                # Campos específicos para la solicitud del docente
                course_full_name=getattr(data, "course_full_name", None),
                course_key=getattr(data, "course_key", None),
                groups=getattr(data, "groups", None),
            )

            db.add(db_account_request)
            db.commit()
            db.refresh(db_account_request)

            return {"message": "Solicitud de cuenta procesada exitosamente"}

        except SQLAlchemyError:
            db.rollback()
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
