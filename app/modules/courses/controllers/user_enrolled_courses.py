"""
Módulo UserEnrolledCoursesController - Gestión de Dashboard Académico

Este controlador es responsable de recuperar y enriquecer la lista de cursos
en los que un usuario está matriculado activamente. Su función principal es
servir de puente entre la identidad de Keycloak (kc_id) y el ecosistema de
Moodle, añadiendo metadatos de roles por cada curso obtenido.
"""

from fastapi import HTTPException
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.orm import Session

from app.modules.courses.services.moodle_service import MoodleService
from app.shared.dependecies.get_current_user import CurrentUser
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.models.users_model import UserAccounts
from app.shared.services.moodle_service import MoodleService as SharedMoodleService


class UserEnrolledCoursesController:
    """
    Controlador para la obtención de la oferta académica personalizada del usuario.
    Centraliza la lógica de resolución de IDs y enriquecimiento de perfiles.
    """

    @staticmethod
    async def get_user_enrolled_courses(
        institute: InstitutesEnum, user_info: CurrentUser, db: Session
    ) -> list:
        """
        Obtiene todos los cursos donde el usuario está inscrito en un instituto dado.

        Flujo de ejecución:
        1. Resuelve el moodle_id local mediante el kc_id del token.
        2. Consulta a la API de Moodle los cursos inscritos.
        3. Enriquecimiento: Para cada curso, consulta el rol (teacher, student, etc.).
        """
        # 1. Obtención de identidad cruzada (Keycloak ID -> Moodle ID)
        user_id = await UserEnrolledCoursesController._get_moodle_id_from_user_info(
            user_info, db
        )

        # 2. Consulta de cursos en el LMS
        enrolled_courses_result = await MoodleService.get_enrolled_courses(
            institute=institute, user_id=user_id
        )

        if enrolled_courses_result.error:
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "MOODLE_ERROR",
                    "message": f"No se pudieron obtener los cursos para el usuario {user_id} en {institute.value}",
                },
            )

        # 3. Inyección de roles específicos por curso
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
        """
        Método interno para resolver la vinculación de cuentas.

        Busca en la tabla UserAccounts el registro que coincida con el UUID de Keycloak.
        Lanza excepciones controladas si el usuario no existe o no ha sido sincronizado
        con Moodle aún.
        """
        kc_id = user_info.kc_id

        try:
            query = db.query(UserAccounts).filter(UserAccounts.kc_id == kc_id).one()

            if not query.moodle_id:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error_code": "MOODLE_NO_ENCONTRADO",
                        "message": "El usuario existe localmente pero no tiene una cuenta vinculada en Moodle.",
                    },
                )
            return query.moodle_id

        except NoResultFound:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "NO_ENCONTRADO",
                    "message": "La identidad de Keycloak no corresponde a ningún usuario en MACTI.",
                },
            ) from NoResultFound
        except MultipleResultsFound:
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "MULTIPLES_RESULTADOS",
                    "message": "Error de integridad: se encontró más de una cuenta para esta identidad.",
                },
            ) from MultipleResultsFound

    @classmethod
    async def _add_role_to_courses(
        cls, institute: InstitutesEnum, courses: list, user_id: int
    ) -> list:
        """
        Inyecta el 'shortname' del rol de Moodle en la estructura de cada curso.

        Realiza una petición por cada curso para obtener el perfil del usuario
        dentro de ese contexto académico. Si falla, asigna por defecto el rol 'student'.
        """
        for course in courses:
            get_user_profile = await SharedMoodleService.get_user_profile(
                institute=institute, user_id=user_id, course_id=course["id"]
            )

            # Extraemos los shortnames de los roles (ej: 'editingteacher', 'student')
            course["role"] = (
                [role["shortname"] for role in get_user_profile.user_profile["roles"]]
                if get_user_profile.error is None
                and get_user_profile.user_profile
                and get_user_profile.user_profile.get("roles")
                else ["student"]
            )

        return courses
