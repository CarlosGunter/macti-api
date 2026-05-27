# Módulo UserEnrolledCoursesController - Gestión de Dashboard Académico
#
# Este controlador es responsable de recuperar y enriquecer la lista de cursos
# en los que un usuario está matriculado activamente. Su función principal es
# servir de puente entre la identidad de Keycloak (kc_id) y el ecosistema de
# Moodle, añadiendo metadatos de roles por cada curso obtenido.

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.courses.repositories.user_enrolled_courses_repository import (
    UserEnrolledCoursesRepository,
)
from app.modules.courses.services.moodle_service import MoodleService
from app.shared.dependecies.get_current_user import CurrentUser
from app.shared.enums.institutes_enum import InstitutesEnum
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
        repo = UserEnrolledCoursesRepository(db)
        user_id = await UserEnrolledCoursesController._resolve_moodle_id(
            repo, user_info
        )

        # 2. Consulta de cursos en el LMS
        enrolled_courses = await UserEnrolledCoursesController._fetch_enrolled_courses(
            institute, user_id
        )

        # 3. Inyección de roles específicos por curso
        enriched = await UserEnrolledCoursesController._add_role_to_courses(
            institute=institute, courses=enrolled_courses, user_id=user_id
        )

        return enriched

    @classmethod
    async def _resolve_moodle_id(
        cls, repo: UserEnrolledCoursesRepository, user_info: CurrentUser
    ) -> int:
        """Resuelve el `moodle_id` local a partir del `kc_id` del request.

        Usa el repositorio para obtener todas las filas asociadas y gestiona
        los casos: 0 resultados, múltiples resultados o resultado sin `moodle_id`.
        """
        kc_id = user_info.kc_id

        matches = repo.get_jids_by_kc_id(kc_id)
        if not matches:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "MOODLE_NO_ENCONTRADO",
                    "message": "La identidad de Keycloak no corresponde a ningún usuario en MACTI.",
                },
            )

        if len(matches) > 1:
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "MULTIPLES_RESULTADOS",
                    "message": "Error de integridad: se encontró más de una cuenta para esta identidad.",
                },
            )

        entry = matches[0]
        if not entry.auth or entry.moodle_id is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "MOODLE_NO_ENCONTRADO",
                    "message": "El usuario existe localmente pero no tiene una cuenta vinculada en Moodle.",
                },
            )

        return entry.moodle_id

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
            try:
                get_user_profile = await SharedMoodleService.get_user_profile(
                    institute=institute, user_id=user_id, course_id=course["id"]
                )

                if (
                    get_user_profile.error
                    or not get_user_profile.user_profile
                    or not get_user_profile.user_profile.get("roles")
                ):
                    course["role"] = ["student"]
                else:
                    course["role"] = [
                        role["shortname"]
                        for role in get_user_profile.user_profile["roles"]
                    ]
            except Exception:
                course["role"] = ["student"]

        return courses

    @staticmethod
    async def _fetch_enrolled_courses(institute: InstitutesEnum, user_id: int) -> list:
        """Llama a la capa de servicio de Moodle y normaliza respuesta o lanza HTTPException."""
        result = await MoodleService.get_enrolled_courses(
            institute=institute, user_id=user_id
        )
        if getattr(result, "error", None):
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "MOODLE_ERROR",
                    "message": f"No se pudieron obtener los cursos para el usuario {user_id} en {institute.value}",
                },
            )

        return getattr(result, "enrolled_courses", [])
