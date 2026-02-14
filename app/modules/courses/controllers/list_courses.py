# Módulo ListCoursesController - Consulta de Oferta Académica
#
# Este controlador actúa como un puente de consulta directa hacia las instancias de
# Moodle. Su propósito es recuperar el catálogo completo de cursos configurados
# en un instituto específico, permitiendo que la interfaz de MACTI presente la
# oferta académica actualizada en tiempo real.

from fastapi import HTTPException

from app.modules.courses.services.moodle_service import MoodleService
from app.shared.enums.institutes_enum import InstitutesEnum


class ListCoursesController:
    """
    Controlador encargado de gestionar la recuperación de metadatos de cursos
    alojados en plataformas externas (Moodle).
    """

    @staticmethod
    async def list_courses(institute: InstitutesEnum):
        """
        Lista todos los cursos disponibles en la plataforma Moodle para un instituto específico.

        Proceso:
        1. Invoca al servicio MoodleService para realizar una petición asíncrona.
        2. Valida la respuesta del Web Service de Moodle.
        3. En caso de éxito, retorna una lista de objetos de curso (id, fullname, shortname, etc.).

        Errores:
            Lanza una excepción 502 (Bad Gateway) si la comunicación con Moodle falla
            o si el token de administración no tiene permisos de lectura.
        """

        # Consumo del servicio de Moodle especializado en lectura de catálogo
        courses = await MoodleService.get_courses(institute=institute)

        # Manejo de errores provenientes del Web Service
        if courses.error:
            # Si el servicio retorna un error, se propaga al cliente con un código
            # estandarizado para que el front-end pueda mostrar una alerta adecuada.
            raise HTTPException(
                status_code=502,
                detail={
                    "error_code": "MOODLE_COURSE_LIST_ERROR",
                    "message": courses.error,
                },
            )

        # Retorna el listado de cursos directamente.
        # Moodle suele retornar: id, shortname, fullname, displayname e idnumber.
        return courses.courses
