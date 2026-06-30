"""
Service for interacting with Moodle LMS API - Project MACTI
"""

from types import SimpleNamespace

from app.shared.config.moodle_configs import MOODLE_CONFIG
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.services.moodle_client import make_moodle_request
from app.shared.services.redis_client import redis_client


class MoodleService:
    """
    Clase estática que centraliza las operaciones de lectura y escritura en Moodle.
    Incluye gestión de usuarios, inscripciones y creación dinámica de espacios (cursos).

    Las operaciones de lectura utilizan caché Redis para reducir llamadas a la API externa.
    Las operaciones de escritura invalidan el caché relacionado para mantener consistencia.
    """

    @staticmethod
    async def get_user_profile_by_email(institute: InstitutesEnum, user_email: str):
        """
        Busca un usuario en el LMS utilizando su dirección de correo electrónico.

        Útil para la sincronización inicial de cuentas cuando el usuario ya existe
        en Moodle pero no en la base de datos local de MACTI.

        Resultado cacheado para evitar llamadas repetidas a Moodle.
        """
        # Intentar obtener del caché
        cache_key = redis_client.build_key(
            "user_profile_by_email",
            institute=institute.value,
            email=user_email.lower(),
        )
        cached = await redis_client.get(cache_key)
        if cached:
            return SimpleNamespace(user_profile=cached, error=None)

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
        user_profile = result["data"][0] if result["data"] else {}

        # Guardar en caché si se encontró
        if user_profile:
            await redis_client.set(cache_key, user_profile)

        return SimpleNamespace(
            user_profile=user_profile,
            error=None,
        )

    @staticmethod
    async def get_user_profile(institute: InstitutesEnum, user_id: int, course_id: int):
        """
        Obtiene el perfil detallado de un usuario dentro del contexto de un curso.

        Este método es clave para recuperar los ROLES (Student, Teacher, etc.)
        que el usuario desempeña en una materia específica.

        Resultado cacheado para evitar llamadas repetidas a Moodle.
        """
        # Intentar obtener del caché
        cache_key = redis_client.build_key(
            "user_profile",
            institute=institute.value,
            user_id=user_id,
            course_id=course_id,
        )
        cached = await redis_client.get(cache_key)
        if cached:
            return SimpleNamespace(user_profile=cached, error=None)

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

        # Guardar en caché si se encontró
        if user_profile:
            await redis_client.set(cache_key, user_profile)

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

        Resultado cacheado para evitar llamadas repetidas a Moodle.
        """
        # Intentar obtener del caché
        cache_key = redis_client.build_key(
            "course_by_shortname",
            institute=institute.value,
            shortname=shortname.lower(),
        )
        cached = await redis_client.get(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]  # ya es int | None guardado

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

        course_id = None
        if (
            result["success"]
            and result["data"]
            and len(result["data"].get("courses", [])) > 0
        ):
            course_id = result["data"]["courses"][0]["id"]

        # Guardar en caché (incluso None para no repetir búsquedas fallidas)
        await redis_client.set(cache_key, course_id)

        return course_id

    @staticmethod
    async def get_assignment_id_by_name(
        course_id: int, assignment_name: str, institute: InstitutesEnum
    ) -> int | None:
        """
        Busca el ID de una tarea específica dentro de un curso utilizando su nombre exacto.

        Resultado cacheado para evitar llamadas repetidas a Moodle.
        """
        # Intentar obtener del caché
        cache_key = redis_client.build_key(
            "assignment_by_name",
            institute=institute.value,
            course_id=course_id,
            assignment_name=assignment_name.lower().strip(),
        )
        cached = await redis_client.get(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]  # ya es int | None guardado

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

        assignment_id = None
        if result["success"] and result["data"] and "courses" in result["data"]:
            for course in result["data"]["courses"]:
                if course["id"] == course_id:
                    for assign in course.get("assignments", []):
                        if (
                            assign["name"].strip().lower()
                            == assignment_name.strip().lower()
                        ):
                            assignment_id = assign["id"]
                            break

        # Guardar en caché (incluso None para no repetir búsquedas fallidas)
        await redis_client.set(cache_key, assignment_id)

        return assignment_id

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

        Invalida el caché de asignaciones del curso para mantener consistencia.
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
            # Invalidar caché de asignaciones de este curso
            await redis_client.delete_pattern(
                f"moodle:assignment_by_name:*{institute.value}*{course_id}*"
            )
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

        Resultado cacheado para evitar llamadas repetidas a Moodle.
        """
        # Intentar obtener del caché
        cache_key = redis_client.build_key(
            "user_courses",
            institute=institute.value,
            moodle_userid=moodle_userid,
        )
        cached = await redis_client.get(cache_key)
        if cached:
            return SimpleNamespace(courses=cached, error=None)

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

        courses = result["data"] if isinstance(result["data"], list) else []

        # Guardar en caché
        await redis_client.set(cache_key, courses)

        return SimpleNamespace(
            courses=courses,
            error=None,
        )
