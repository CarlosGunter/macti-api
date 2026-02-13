from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.auth.services.kc_service import KeycloakService
from app.modules.auth.services.moodle_service import MoodleService
from app.shared.enums.status_enum import AccountStatusEnum
from app.shared.models.users_model import UserAccounts
from app.shared.models.verification_tokens_model import VerificationToken

from ..schema import CreateAccountSchema


class CreateAccountController:
    @staticmethod
    async def create_account(data: CreateAccountSchema, db: Session):
        """
        Orquesta la creación de cuenta en Keycloak y Moodle.

        Parámetros:
            data: Contiene el user_id de la solicitud y la nueva contraseña.
            db: Sesión activa de la base de datos.

        Flujo:
            1. Verifica existencia y estatus 'APPROVED' de la solicitud.
            2. Crea el usuario en Keycloak (IDM).
            3. Crea el usuario en Moodle (LMS).
            4. Realiza el 'rollback' en Keycloak si Moodle falla (Integridad).
            5. Inscribe al usuario en el curso.
            6. Limpia tokens de verificación usados.
        """

        # 1. Validación de la solicitud en base de datos local
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

        # Seguridad: Solo solicitudes validadas por el Admin y el usuario pueden proceder
        if account_request.status != AccountStatusEnum.APPROVED:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "STATUS_INVALIDO",
                    "message": "La solicitud debe estar aprobada antes de crear la cuenta",
                },
            )

        # 2. Aprovisionamiento en Keycloak (Identidad y Credenciales)
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
                    "message": f"Error creando usuario en Keycloak: {kc_result.get('error')}",
                },
            )

        # Guardamos el UUID generado por Keycloak para futuras referencias
        account_request.kc_id = UUID(kc_result.get("user_id"))

        # 3. Aprovisionamiento en Moodle (Perfil de Estudiante/Docente)
        moodle_result = await MoodleService.create_user(
            user_data={
                "name": account_request.name,
                "last_name": account_request.last_name,
                "email": account_request.email,
                "course_id": account_request.course_id,
            },
            institute=account_request.institute,
        )

        # Manejo de fallos en cascada (Circuit Breaker manual)
        if not moodle_result.get("created"):
            """
            Si Moodle falla, debemos eliminar al usuario recién creado en Keycloak
            para mantener los sistemas sincronizados y permitir un re-intento limpio.
            """
            await KeycloakService.delete_user(
                user_id=str(account_request.kc_id),
                institute=account_request.institute,
            )

            raise HTTPException(
                status_code=502,
                detail={
                    "error_code": "MOODLE_ERROR",
                    "message": "Error creando usuario en Moodle. Se revirtieron cambios en Keycloak.",
                },
            )

        # Guardamos el ID interno de Moodle para el usuario
        account_request.moodle_id = moodle_result.get("id")

        # 4. Inscripción Automática al curso solicitado
        await MoodleService.enroll_user(
            user_id=moodle_result["id"],
            course_id=account_request.course_id,
            institute=account_request.institute,
        )

        # 5. Finalización y Limpieza
        # Marcamos la solicitud como 'CREATED' (Proceso finalizado)
        account_request.status = AccountStatusEnum.CREATED

        # Eliminamos el token de verificación ya que no es más necesario
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
            "message": "Cuenta creada y vinculada exitosamente en Keycloak y Moodle",
            "kc_id": str(account_request.kc_id),
            "moodle_id": account_request.moodle_id,
        }
