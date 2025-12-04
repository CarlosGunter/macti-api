from fastapi import HTTPException
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.orm import Session

from app.modules.auth.models import AccountRequest
from app.modules.courses.services.moodle_service import MoodleService
from app.shared.dependecies.get_current_user import CurrentUser
from app.shared.enums.institutes_enum import InstitutesEnum


class UserEnrolledCoursesController:
    """Retorna los cursos en los que un usuario está inscrito."""

    @staticmethod
    async def get_user_enrolled_courses(
        institute: InstitutesEnum, user_info: CurrentUser, db: Session
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

        enrolled_courses_result.enrolled_courses = (
            await UserEnrolledCoursesController._add_role_to_courses(
                institute=institute,
                courses=enrolled_courses_result.enrolled_courses,
                user_id=user_id,
            )
        )

        return enrolled_courses_result.enrolled_courses

    @classmethod
    async def _get_moodle_id_from_user_info(
        cls, user_info: CurrentUser, db: Session
    ) -> int:
        """Extrae el ID de Moodle del usuario a partir de la información del token."""
        kc_id = user_info.kc_id

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
            return query.moodle_id

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

    @classmethod
    async def _add_role_to_courses(
        cls, institute: InstitutesEnum, courses: list, user_id: int
    ) -> list:
        """Agrega el rol del usuario a cada curso en la lista."""
        for course in courses:
            get_user_profile = await MoodleService.get_user_profile(
                institute=institute, user_id=user_id, course_id=course["id"]
            )

            course["role"] = (
                get_user_profile.user_profile["roles"][0]["shortname"]
                if get_user_profile.error is None
                and get_user_profile.user_profile
                and get_user_profile.user_profile.get("roles")
                else "student"
            )

        return courses
