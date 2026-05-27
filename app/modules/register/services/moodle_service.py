"""
Service for interacting with Moodle LMS API
"""

from dataclasses import dataclass, field

from app.shared.config.moodle_configs import MOODLE_CONFIG
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.enums.role_moodle_enum import RoleEnum
from app.shared.services.moodle_client import make_moodle_request
from app.shared.services.moodle_service import MoodleService as BaseMoodleService


@dataclass
class CreateUserResult:
    created: bool
    user_id: int | None = None
    error: str | None = None


@dataclass
class EnrollUserResult:
    enrolled: bool
    user_id: int | None = None
    course_id: int | None = None
    error: str | None = None
    warning: str | None = None


@dataclass
class DeleteUserResult:
    deleted: bool
    user_id: int | None = None
    error: str | None = None


@dataclass
class GetAdminsResult:
    success: bool
    error_message: str | None = None
    admins: list = field(default_factory=list)


@dataclass
class CreateCourseResult:
    course_ids: list[int] = field(default_factory=list)
    error: str | None = None


@dataclass
class CreateGroupResult:
    group: dict | None = None
    error: str | None = None


class MoodleService:
    """
    Clase estática que centraliza las operaciones de lectura y escritura en Moodle.
    """

    @staticmethod
    async def create_user(
        user_data: dict, institute: InstitutesEnum
    ) -> CreateUserResult:
        """
        Crea un nuevo usuario en la instancia de Moodle correspondiente.
        """
        config = MOODLE_CONFIG[institute]
        endpoint = config.moodle_url
        params = {
            "wstoken": config.moodle_token,
            "wsfunction": "core_user_create_users",
            "moodlewsrestformat": "json",
        }

        # Estructura de datos requerida por el Web Service de Moodle
        data = {
            "users[0][username]": user_data["email"],
            "users[0][firstname]": user_data.get("name", "User"),
            "users[0][lastname]": user_data.get("last_name", "NA"),
            "users[0][email]": user_data["email"],
            "users[0][auth]": "oauth2",
        }

        print(
            f"DEBUG: Enviando creación de usuario a Moodle ({institute.value}): {user_data['email']}"
        )

        result_response = await make_moodle_request(
            url=endpoint,
            params=params,
            data=data,
            institute=institute,
        )

        if not result_response["success"]:
            return CreateUserResult(
                created=False, error=result_response["error_message"]
            )

        result = result_response["data"]
        user_id = (
            result[0].get("id")
            if isinstance(result, list) and len(result) > 0
            else None
        )
        user_id = int(user_id) if user_id is not None else None

        if user_id is None:
            return CreateUserResult(
                created=False, error="ID de usuario no retornado por Moodle"
            )
        # Moodle retorna una lista de diccionarios con los IDs de los usuarios creados.
        return CreateUserResult(created=True, user_id=user_id)

    @staticmethod
    async def enroll_user(
        user_id: int, course_id: int, institute: InstitutesEnum, role_id: int = 5
    ) -> EnrollUserResult:
        """
        Matricula a un usuario existente en un curso específico de Moodle con un rol dinámico.
        """
        enrollment_status = await BaseMoodleService.is_user_enrolled_in_course(
            institute=institute, user_id=user_id, course_id=course_id
        )

        if enrollment_status.error:
            return EnrollUserResult(
                enrolled=False,
                error=enrollment_status.error,
            )

        if enrollment_status.is_enrolled:
            return EnrollUserResult(
                enrolled=False,
                error="El usuario ya está inscrito en este curso",
            )

        config = MOODLE_CONFIG[institute]
        endpoint = config.moodle_url
        params = {
            "wstoken": config.moodle_token,
            "wsfunction": "enrol_manual_enrol_users",
            "moodlewsrestformat": "json",
        }

        data = {
            "enrolments[0][roleid]": role_id,
            "enrolments[0][userid]": user_id,
            "enrolments[0][courseid]": course_id,
            "enrolments[0][suspend]": 0,
        }

        result_response = await make_moodle_request(
            url=endpoint,
            params=params,
            data=data,
            institute=institute,
            # Se desactiva la verificación automática para manejar excepciones manualmente abajo
            check_moodle_errors=False,
        )

        if not result_response["success"]:
            return EnrollUserResult(
                enrolled=False,
                error=f"Fallo de conexión/petición: {result_response['error_message']}",
            )

        result = result_response["data"]

        # Manejo de Excepciones de Moodle:
        # Moodle puede retornar un 200 OK pero con un cuerpo de 'exception'.
        if isinstance(result, dict) and "exception" in result:
            if result.get("message") == "error/Message was not sent.":
                print(
                    f"AVISO: Usuario {user_id} matriculado, pero Moodle no pudo enviar el email de aviso."
                )
                return EnrollUserResult(
                    user_id=user_id,
                    course_id=course_id,
                    enrolled=True,
                    warning="Matrícula exitosa con error de notificación SMTP en Moodle",
                )

            return EnrollUserResult(
                enrolled=False,
                error=f"Error de Moodle: {result.get('message', 'Desconocido')}",
            )

        return EnrollUserResult(user_id=user_id, course_id=course_id, enrolled=True)

    @staticmethod
    async def delete_user(user_id: int, institute: InstitutesEnum) -> DeleteUserResult:
        """
        Delete a user in Moodle using the REST API.
        """
        config = MOODLE_CONFIG[institute]
        endpoint = config.moodle_url
        params = {
            "wstoken": config.moodle_token,
            "wsfunction": "core_user_delete_users",
            "moodlewsrestformat": "json",
        }

        data = {
            "userids[0]": str(user_id),
        }

        result_response = await make_moodle_request(
            url=endpoint,
            params=params,
            data=data,
            institute=institute,
        )

        if not result_response["success"]:
            return DeleteUserResult(
                deleted=False,
                error=result_response["error_message"],
            )

        return DeleteUserResult(deleted=True, user_id=user_id)

    @staticmethod
    async def get_user_roles(
        institute: InstitutesEnum,
        course_id: int,
        moodle_id: int,
    ) -> list[RoleEnum]:
        """
        Función auxiliar para recuperar roles asignados en un curso de Moodle.
        """

        get_user_profile_result = await BaseMoodleService.get_user_profile(
            institute=institute, user_id=moodle_id, course_id=course_id
        )

        if get_user_profile_result.error:
            return []

        user_roles = get_user_profile_result.user_profile.get("roles", [])

        # Conversión de IDs numéricos de Moodle al Enum RoleEnum para tipado fuerte
        list_roles = [RoleEnum(role["roleid"]) for role in user_roles]

        return list_roles

    @staticmethod
    async def get_admins(institute: InstitutesEnum) -> GetAdminsResult:
        """
        Función auxiliar para obtener la lista de emails de administradores de un instituto.
        """
        config = MOODLE_CONFIG[institute]
        endpoint = config.moodle_url

        params = {
            "wstoken": config.moodle_token,
            "wsfunction": "local_sitemanagers_get_site_managers",
            "moodlewsrestformat": "json",
        }

        result_response = await make_moodle_request(
            url=endpoint,
            params=params,
            institute=institute,
        )
        if not result_response["success"]:
            return GetAdminsResult(
                success=False,
                error_message=result_response["error_message"],
                admins=[],
            )

        return GetAdminsResult(
            success=True,
            error_message=None,
            admins=result_response.get("data", []),
        )

    @staticmethod
    async def create_courses(
        institute: InstitutesEnum,
        fullname: str,
        groups: list[str],
        summary: str = "",
        category_id: int = 1,
    ) -> CreateCourseResult:
        """
        Automatiza la creación de uno o varios cursos en Moodle en una sola llamada.
        """
        config = MOODLE_CONFIG[institute]
        endpoint = config.moodle_url
        params = {
            "wstoken": config.moodle_token,
            "wsfunction": "core_course_create_courses",
            "moodlewsrestformat": "json",
        }

        # Lambda interno para generar el shortname por curso usando la lógica del proyecto
        shortname_lambda = (  # noqa: E731
            lambda group: (
                f"{institute.value[:3].upper()}-"
                f"{
                    (
                        ''.join([w[0] for w in fullname.split()[:3]]).upper()
                        if len(fullname.split()) >= 2
                        else fullname[:3].upper()
                    )
                }-"
                f"{str(group).upper() if group else '0'}"
            )
        )

        data = {}
        for index, group in enumerate(groups):
            course_shortname = shortname_lambda(group)

            data[f"courses[{index}][fullname]"] = f"{fullname} - {group}"
            data[f"courses[{index}][shortname]"] = course_shortname
            data[f"courses[{index}][categoryid]"] = category_id
            data[f"courses[{index}][idnumber]"] = course_shortname
            data[f"courses[{index}][summary]"] = summary
            data[f"courses[{index}][format]"] = "topics"

        result_response = await make_moodle_request(
            url=endpoint,
            params=params,
            data=data,
            institute=institute,
        )

        if not result_response["success"]:
            return CreateCourseResult(
                course_ids=[], error=result_response["error_message"]
            )

        result = result_response.get("data", [])
        if not isinstance(result, list):
            return CreateCourseResult(
                course_ids=[],
                error="Respuesta inesperada de Moodle al crear cursos",
            )

        course_ids = [
            course["id"]
            for course in result
            if isinstance(course, dict) and "id" in course
        ]

        return CreateCourseResult(course_ids=course_ids, error=None)
