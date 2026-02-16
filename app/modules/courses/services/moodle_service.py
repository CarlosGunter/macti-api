# Módulo MoodleService - Consultas Académicas
#
# Este servicio se especializa en la recuperación de información desde las instancias
# de Moodle. Proporciona métodos para listar el catálogo global de cursos y para
# consultar la relación específica de cursos asociados a un usuario (inscripciones).

from types import SimpleNamespace

from app.shared.config.moodle_configs import MOODLE_CONFIG
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.services.moodle_client import make_moodle_request


class MoodleService:
    """
    Clase encargada de la comunicación de lectura con los Web Services de Moodle.
    """

    @staticmethod
    async def get_courses(institute: InstitutesEnum, ids: list[int] | None = None):
        """
        Recupera la lista completa de cursos disponibles en un instituto.

        Utiliza la función 'core_course_get_courses' de Moodle para traer
        metadatos como nombres, categorías e IDs de todos los cursos visibles.

        Retorna:
            SimpleNamespace: Con los atributos .courses (lista) y .error (str o None).
        """
        config = MOODLE_CONFIG[institute]
        params = {
            "wstoken": config.moodle_token,
            "wsfunction": "core_course_get_courses",
            "moodlewsrestformat": "json",
        }

        data = {} if ids else None
        for i, course_id in enumerate(ids or []):
            if data is not None:
                data[f"options[ids][{i}]"] = course_id

        # Ejecución de la petición a través del cliente asíncrono compartido
        result = await make_moodle_request(
            url=config.moodle_url,
            params=params,
            institute=institute,
            data=data,
        )

        if not result["success"]:
            return SimpleNamespace(
                courses=[],
                error=result["error_message"],
            )

        return SimpleNamespace(
            courses=result["data"],
            error=None,
        )

    @staticmethod
    async def get_enrolled_courses(institute: InstitutesEnum, user_id: int):
        """
        Consulta los cursos en los que un usuario específico está inscrito.

        A diferencia del listado global, esta consulta ('core_enrol_get_users_courses')
        requiere un 'userid' y retorna únicamente los cursos vinculados a ese perfil.

        Retorna:
            SimpleNamespace: Con los atributos .enrolled_courses (lista) y .error (str o None).
        """
        config = MOODLE_CONFIG[institute]
        params = {
            "wstoken": config.moodle_token,
            "wsfunction": "core_enrol_get_users_courses",
            "moodlewsrestformat": "json",
            "userid": user_id,
        }

        result = await make_moodle_request(
            url=config.moodle_url,
            params=params,
            institute=institute,
        )

        if not result["success"]:
            return SimpleNamespace(
                enrolled_courses=[],
                error=result["error_message"],
            )

        return SimpleNamespace(
            enrolled_courses=result["data"],
            error=None,
        )
