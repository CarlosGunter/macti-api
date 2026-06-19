"""
Service for interacting with Moodle LMS API - Project MACTI
"""

from types import SimpleNamespace

from app.shared.config.moodle_configs import MOODLE_CONFIG
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.services.moodle_client import make_moodle_request


class MoodleService:
    """
    Clase estática que centraliza las operaciones de lectura y escritura en Moodle.
    Incluye gestión de usuarios, inscripciones y creación dinámica de espacios (cursos).
    """

    @staticmethod
    async def get_user_profile_by_email(institute: InstitutesEnum, user_email: str):
        """
        Busca un usuario en el LMS utilizando su dirección de correo electrónico.

        Útil para la sincronización inicial de cuentas cuando el usuario ya existe
        en Moodle pero no en la base de datos local de MACTI.
        """
        config = MOODLE_CONFIG[institute]
        params = {
            "wstoken": config.moodle_token,
            "wsfunction": "core_user_get_users_by_field",
            "moodlewsrestformat": "json",
        }
        data = {"field": "email", "values[0]": user_email}

        result = await make_moodle_request(
            url=config.moodle_url,
            params=params,
            data=data,
            institute=institute,
        )

        if not result["success"]:
            return SimpleNamespace(
                user_profile={},
                error=result["error_message"],
            )

        # Moodle retorna una lista; si hay coincidencia, tomamos el primer resultado
        return SimpleNamespace(
            user_profile=result["data"][0] if result["data"] else {},
            error=None,
        )

    @staticmethod
    async def get_user_profile(institute: InstitutesEnum, user_id: int, course_id: int):
        """
        Obtiene el perfil detallado de un usuario dentro del contexto de un curso.

        Este método es clave para recuperar los ROLES (Student, Teacher, etc.)
        que el usuario desempeña en una materia específica.
        """
        config = MOODLE_CONFIG[institute]
        params = {
            "wstoken": config.moodle_token,
            "wsfunction": "core_user_get_course_user_profiles",
            "moodlewsrestformat": "json",
        }

        data = {
            "userlist[0][courseid]": course_id,
            "userlist[0][userid]": user_id,
        }

        result = await make_moodle_request(
            url=config.moodle_url,
            params=params,
            data=data,
            institute=institute,
        )

        if not result["success"]:
            return SimpleNamespace(
                user_profile=None,
                error=result["error_message"],
            )

        user_profiles = result["data"]
        user_profile = user_profiles[0] if user_profiles else None

        return SimpleNamespace(
            user_profile=user_profile,
            error=None,
        )

    @staticmethod
    async def get_user_by_email(email: str, institute: InstitutesEnum) -> int | None:
        """
        Reutiliza la función existente para obtener únicamente el ID del usuario.
        """
        res = await MoodleService.get_user_profile_by_email(institute, email)
        if res.error is None and res.user_profile:
            return res.user_profile.get("id")
        return None

    @staticmethod
    async def get_course_by_shortname(
        shortname: str, institute: InstitutesEnum
    ) -> int | None:
        """
        Busca un curso por su nombre corto y devuelve su ID en Moodle.
        """
        config = MOODLE_CONFIG[institute]
        params = {
            "wstoken": config.moodle_token,
            "wsfunction": "core_course_get_courses_by_field",
            "moodlewsrestformat": "json",
        }
        data = {"field": "shortname", "value": shortname}

        result = await make_moodle_request(
            url=config.moodle_url,
            params=params,
            data=data,
            institute=institute,
        )

        if (
            result["success"]
            and result["data"]
            and len(result["data"].get("courses", [])) > 0
        ):
            return result["data"]["courses"][0]["id"]
        return None

    @staticmethod
    async def get_assignment_id_by_name(
        course_id: int, assignment_name: str, institute: InstitutesEnum
    ) -> int | None:
        """
        Busca el ID de una tarea específica dentro de un curso utilizando su nombre exacto.
        """
        config = MOODLE_CONFIG[institute]
        params = {
            "wstoken": config.moodle_token,
            "wsfunction": "mod_assign_get_assignments",
            "moodlewsrestformat": "json",
        }
        data = {"courseids[0]": course_id}

        result = await make_moodle_request(
            url=config.moodle_url,
            params=params,
            data=data,
            institute=institute,
        )

        if result["success"] and result["data"] and "courses" in result["data"]:
            for course in result["data"]["courses"]:
                if course["id"] == course_id:
                    for assign in course.get("assignments", []):
                        if (
                            assign["name"].strip().lower()
                            == assignment_name.strip().lower()
                        ):
                            return assign["id"]
        return None

    @staticmethod
    async def update_grade(
        institute: InstitutesEnum,
        course_id: int,  # noqa: ARG004
        assignment_id: int,
        moodle_userid: int,
        grade: float,
    ) -> dict:
        """
        Actualiza o inserta la calificación de un usuario en una tarea específica.
        """
        config = MOODLE_CONFIG[institute]
        params = {
            "wstoken": config.moodle_token,
            "wsfunction": "mod_assign_save_grade",
            "moodlewsrestformat": "json",
        }
        data = {
            "assignmentid": assignment_id,
            "userid": moodle_userid,
            "grade": grade,
            "attemptnumber": -1,
            "addattempt": 0,
            "workflowstate": "graded",
            "applytoall": 1,
        }

        result = await make_moodle_request(
            url=config.moodle_url,
            params=params,
            data=data,
            institute=institute,
        )

        if result["success"]:
            return {"success": True, "data": result.get("data")}

        return {
            "success": False,
            "error_message": result.get(
                "error_message", "Error desconocido al actualizar calificación"
            ),
        }

    # Función para poder obtener los cursos en los que un usuario está inscrito, utilizando su ID
    # de Moodle. Esta función es útil para el endpoint que consulta los cursos inscritos por
    # usuario, y la llamamos desde el MoodleService del módulo de cursos para reutilizar la lógica
    # de consulta a Moodle. De esta forma, centralizamos toda la lógica de interacción con Moodle
    # dentro del servicio de Shared, y el módulo de cursos simplemente delega la consulta al
    # servicio centralizado.
    @staticmethod
    async def get_user_courses(institute: InstitutesEnum, moodle_userid: int):
        """
        Obtiene la lista de todos los cursos en los que un usuario está inscrito
        dentro de Moodle utilizando su ID de Moodle.
        """
        config = MOODLE_CONFIG[institute]
        params = {
            "wstoken": config.moodle_token,
            "wsfunction": "core_enrol_get_users_courses",
            "moodlewsrestformat": "json",
        }
        data = {"userid": moodle_userid}

        result = await make_moodle_request(
            url=config.moodle_url,
            params=params,
            data=data,
            institute=institute,
        )

        if not result["success"]:
            return SimpleNamespace(
                courses=[],
                error=result["error_message"],
            )

        return SimpleNamespace(
            courses=result["data"] if isinstance(result["data"], list) else [],
            error=None,
        )
