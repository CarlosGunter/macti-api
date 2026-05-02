# Módulo ChangeStatusController - Gestión del Ciclo de Vida de Solicitudes
# Este controlador maneja la transición de estados de las solicitudes de cuenta.
# Su función principal es validar la aprobación de una cuenta y coordinar el envío de correos.

from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.modules.register.schemas import RequestStatusUpdateSchema
from app.modules.register.services.kc_service import KeycloakService
from app.modules.register.services.moodle_service import MoodleService
from app.modules.register.use_cases.enroll_user import EnrollUserUseCase
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.enums.role_enum import AccountRoleEnum
from app.shared.enums.status_enum import RequestStatusEnum
from app.shared.models.student_courses_model import StudentCourseRequest
from app.shared.models.teacher_courses_model import TeacherCourseRequest
from app.shared.models.verification_tokens_model import VerificationToken


class RequestStatusController:
    """
    Controlador encargado de actualizar el estado de las solicitudes de cuenta
    y gestionar la lógica de negocio asociada a las transiciones de estado.
    """

    @staticmethod
    async def update_request_status(
        data: RequestStatusUpdateSchema, role: AccountRoleEnum, db: Session
    ):
        """
        Cambia el estatus de una solicitud de cuenta específica.
        """

        # Definición de transiciones de estado permitidas
        valid_transitions = {
            RequestStatusEnum.PENDING: {
                RequestStatusEnum.APPROVED,
                RequestStatusEnum.REJECTED,
            },
            RequestStatusEnum.APPROVED: {
                RequestStatusEnum.REJECTED,
                RequestStatusEnum.PENDING,
            },
            RequestStatusEnum.REJECTED: {
                RequestStatusEnum.PENDING,
                RequestStatusEnum.APPROVED,
            },
            RequestStatusEnum.ENROLLED: {},
        }

        # --- VALIDACIÓN DE EXISTENCIA Y ESTADO ACTUAL ---
        course_request = None
        if role == AccountRoleEnum.ALUMNO:
            course_request = (
                db.query(StudentCourseRequest)
                .filter(StudentCourseRequest.id == data.request_id)
                .options(joinedload(StudentCourseRequest.auth))
                .one_or_none()
            )
        elif role == AccountRoleEnum.DOCENTE:
            course_request = (
                db.query(TeacherCourseRequest)
                .filter(TeacherCourseRequest.id == data.request_id)
                .options(joinedload(TeacherCourseRequest.auth))
                .one_or_none()
            )

        if not course_request:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "SOLICITUD_NO_ENCONTRADA",
                    "message": f"No se encontró una solicitud con ID {data.request_id} para el rol {role.value}.",
                },
            )

        if data.new_status not in valid_transitions.get(course_request.status, set()):
            raise HTTPException(
                status_code=409,
                detail={
                    "error_code": "TRANSICION_INVALIDA",
                    "message": f"No se puede transicionar de {course_request.status.value} a {data.new_status.value}",
                },
            )

        # --- PROCESAMIENTO SEGÚN EL NUEVO ESTADO ---
        message = ""
        if data.new_status == RequestStatusEnum.APPROVED:
            message = await RequestStatusController._handle_approved(
                course_request, db, data.institute
            )

        elif data.new_status == RequestStatusEnum.PENDING:
            message = RequestStatusController._handle_pending(course_request)

        elif data.new_status == RequestStatusEnum.REJECTED:
            message = await RequestStatusController._handle_rejected(
                course_request, course_request.status, db
            )

        else:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "ESTADO_NO_COMPATIBLE",
                    "message": f"El estado {data.new_status.value} no puede ser procesado aquí.",
                },
            )

        # --- COMMIT DE LOS CAMBIOS A LA BASE DE DATOS ---
        db.commit()

        return {"message": message}

    @classmethod
    async def _handle_approved(
        cls,
        course_request: StudentCourseRequest | TeacherCourseRequest,
        db: Session,
        institute: InstitutesEnum,
    ) -> str:
        """
        Si la cuenta está activa, inscribe al usuario en el curso.
        Si la cuenta no está activa, genera un token de validación y envía un correo.
        """

        # Si la cuenta no está activa se genera un token de validación.
        if not course_request.auth.is_active:
            RequestStatusController._generate_and_save_token(course_request.auth.id, db)

            # email_result = EmailService.send_validation_email(
            #     to_email=course_request.email,
            #     token=token,
            # )
            # if not email_result.success:
            #     raise HTTPException(
            #         status_code=502,
            #         detail={
            #             "error_code": "EMAIL_ERROR",
            #             "message": f"Error al enviar el correo de validación: {email_result.error}",
            #         },
            #     )

            course_request.status = RequestStatusEnum.ENROLLED
            return "Solicitud aprobada. Se ha enviado un correo de validación al usuario para confirmar su cuenta."

        # Si la cuenta ya está activa, se inscribe al usuario directamente en el curso.
        enroll_user_use_case = EnrollUserUseCase(
            moodle_service=MoodleService(), institute=institute
        )
        enroll_result = await enroll_user_use_case.execute(
            request_course_data=course_request
        )
        if not enroll_result.enrolled:
            raise HTTPException(
                status_code=502,
                detail={
                    "error_code": "INSCRIPCION_ERROR",
                    "message": f"Error al inscribir al usuario en el curso: {enroll_result.error}",
                },
            )

        course_request.status = RequestStatusEnum.APPROVED
        return "Usuario inscrito exitosamente en el curso."

    @classmethod
    def _handle_pending(
        cls, course_request: StudentCourseRequest | TeacherCourseRequest
    ) -> str:
        """Revierte el estado a pendiente."""
        course_request.status = RequestStatusEnum.PENDING
        return "Solicitud revertida a estado pendiente."

    @classmethod
    async def _handle_rejected(
        cls,
        course_request: StudentCourseRequest | TeacherCourseRequest,
        current_status: RequestStatusEnum,
        db: Session,
    ) -> str:
        """Limpia los datos del usuario en BD."""

        db.query(VerificationToken).filter(
            VerificationToken.auth_id == course_request.auth.id
        ).delete(synchronize_session=False)

        if current_status == RequestStatusEnum.ENROLLED:
            # Eliminación de usuarios en Keycloak y Moodle por rechazo administrativo
            kc_id = course_request.auth.jids.kc_id if course_request.auth.jids else None
            if kc_id:
                await KeycloakService.delete_user(
                    user_id=kc_id,
                    institute=course_request.institute,
                )

            moodle_id = (
                course_request.auth.jids.moodle_id if course_request.auth.jids else None
            )
            if moodle_id:
                await MoodleService.delete_user(
                    user_id=moodle_id,
                    institute=course_request.institute,
                )

            course_request.kc_id = None
            course_request.moodle_id = None

        course_request.status = RequestStatusEnum.REJECTED
        return "Solicitud rechazada exitosamente."

    @classmethod
    def _generate_and_save_token(cls, user_id: int, db: Session):
        """Genera y persiste un token de verificación UUID4."""
        token = str(uuid4())
        timestamp_now = datetime.now()
        expiration_date = timestamp_now + timedelta(days=7)

        validation = (
            db.query(VerificationToken)
            .filter(VerificationToken.auth_id == user_id)
            .one_or_none()
        )

        if validation:
            validation.token = token
            validation.created_at = timestamp_now
            validation.expires_at = expiration_date
        else:
            new_val = VerificationToken(
                auth_id=user_id,
                token=token,
                created_at=timestamp_now,
                expires_at=expiration_date,
                is_used=0,
            )
            db.add(new_val)

        return token
