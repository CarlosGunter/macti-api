# Módulo MoodleService - Consultas Académicas
#
# Este servicio se especializa en la recuperación de información desde las instancias
# de Moodle. Proporciona métodos para listar el catálogo global de cursos y para
# consultar la relación específica de cursos asociados a un usuario (inscripciones).

from types import SimpleNamespace

from app.shared.config.moodle_configs import MOODLE_CONFIG
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.services.moodle_client import make_moodle_request

# Mandamos a llamar el servicio de shared para reutilizar la lógica de consulta de cursos inscritos por usuario, que es un método que agregamos recientemente en el MoodleService de Shared.
from app.shared.services.moodle_service import MoodleService as SharedMoodleService


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
        config = MOODLE_CONFIG.get(institute, None)
        if not config:
            return SimpleNamespace(
                courses=[],
                error="Configuración de Moodle no encontrada para el instituto especificado.",
            )

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

        Delega la petición al servicio centralizado de shared para reutilizar la lógica
        del ecosistema MACTI.

        Retorna:
            SimpleNamespace: Con los atributos .enrolled_courses (lista) y .error (str o None).
        """
        # Llamamos al nuevo método que agregamos en el MoodleService de Shared
        res = await SharedMoodleService.get_user_courses(
            institute, moodle_userid=user_id
        )

        # Mantenemos el contrato original mapeando .courses de shared a .enrolled_courses
        # para que tus rutas (routes.py) no rompan ni tengan que enterarse del cambio de nombre.
        return SimpleNamespace(
            enrolled_courses=res.courses,
            error=res.error,
        )
