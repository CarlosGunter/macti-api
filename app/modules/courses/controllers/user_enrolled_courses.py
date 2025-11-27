from fastapi import HTTPException
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.orm import Session

from app.modules.auth.models import AccountRequest
from app.modules.courses.services.moodle_service import MoodleService
from app.shared.enums.institutes_enum import InstitutesEnum


class UserEnrolledCoursesController:
    """Retorna los cursos en los que un usuario está inscrito."""

    @staticmethod
    async def get_user_enrolled_courses(
        institute: InstitutesEnum, user_info: dict, db: Session
    ) -> list:
        user_id = await UserEnrolledCoursesController._get_moodle_id_from_user_info(
            user_info, db
        )

        enrolled_courses_result = await MoodleService.get_enrolled_courses(
            institute=institute, user_id=user_id
        )

        if enrolled_courses_result.error:
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "MOODLE_ERROR",
                    "message": f"No se pudieron obtener los cursos inscritos para el usuario {user_id} en {institute}",
                },
            )

        return enrolled_courses_result.enrolled_courses

    @classmethod
    async def _get_moodle_id_from_user_info(cls, user_info: dict, db: Session) -> int:
        """Extrae el ID de Moodle del usuario a partir de la información del token."""
        kc_id = user_info["sub"]

        try:
            query = db.query(AccountRequest).filter(AccountRequest.kc_id == kc_id).one()

            if not query.moodle_id:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error_code": "MOODLE_NO_ENCONTRADO",
                        "message": "El usuario no tiene un ID de Moodle asociado.",
                    },
                )
            return int(query.moodle_id)

        except NoResultFound:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "NO_ENCONTRADO",
                    "message": "Usuario no encontrado en la base de datos.",
                },
            ) from NoResultFound
        except MultipleResultsFound:
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "MULTIPLES_RESULTADOS",
                    "message": "Múltiples usuarios encontrados, error interno.",
                },
            ) from MultipleResultsFound
