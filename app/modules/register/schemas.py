"""Esquemas Pydantic usados por el módulo de registro."""

from pydantic import UUID4, BaseModel, ConfigDict, EmailStr, Field

from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.enums.role_enum import AccountRoleEnum
from app.shared.enums.status_enum import RequestStatusEnum


class AccountBaseSchema(BaseModel):
    """
    Esquema base que encapsula los atributos compartidos entre solicitudes.

    Asegura que cualquier petición de cuenta contenga los datos de identidad
    mínimos y el instituto de procedencia.
    """

    name: str
    last_name: str
    email: EmailStr
    institute: InstitutesEnum


class StudentRequestSchema(AccountBaseSchema):
    """
    Esquema para la solicitud de cuenta de ALUMNO.

    Hereda de AccountBaseSchema y añade la restricción de curso obligatorio,
    validando que el ID sea un entero positivo mayor a cero.
    """

    course_id: int = Field(
        ...,
        gt=0,
        description="El ID del curso es obligatorio para la inscripción de alumnos",
    )


class AuthenticatedStudentRequestSchema(BaseModel):
    """Esquema para una solicitud de curso de un alumno ya autenticado."""

    course_id: int = Field(
        ...,
        gt=0,
        description="ID del curso al que el alumno autenticado desea unirse",
    )


class TeacherRequestSchema(AccountBaseSchema):
    """
    Esquema para la solicitud de cuenta de DOCENTE.

    Incluye los metadatos necesarios para la creación de un nuevo espacio
    en Moodle (Course Full Name, Key y Groups). Si 'course_id' es nulo,
    el sistema interpreta una solicitud de creación de curso nuevo.
    """

    course_full_name: str
    groups: list[str] = Field(
        default_factory=list,
        description="Lista de grupos a crear en Moodle. Puede estar vacía.",
    )


class AccountRequestResponse(BaseModel):
    """
    Modelo de respuesta tras el registro de una solicitud.

    Configurado para permitir la creación desde objetos de base de datos (ORM)
    gracias a 'from_attributes=True'.
    """

    message: str
    model_config = ConfigDict(from_attributes=True)


class AccountsResponse(BaseModel):
    """
    Esquema para la visualización administrativa de solicitudes.

    Mapea directamente los campos de la tabla UserAccounts para ser consumidos
    por tablas o listas en el panel de administración.
    """

    id: int
    name: str
    last_name: str
    email: EmailStr
    status: RequestStatusEnum
    model_config = ConfigDict(from_attributes=True)


ListAccountsResponse = list[AccountsResponse]


class TeacherRequestUserResponse(BaseModel):
    """Datos públicos del usuario docente asociado a la solicitud."""

    id: int
    name: str
    last_name: str
    email: EmailStr
    role: AccountRoleEnum
    institute: InstitutesEnum
    model_config = ConfigDict(from_attributes=True)


class TeacherRequestCourseResponse(BaseModel):
    """Datos de la solicitud de curso del docente."""

    id: int
    status: RequestStatusEnum
    course_full_name: str
    groups: list[str]
    model_config = ConfigDict(from_attributes=True)


class TeacherRequestAccountResponse(BaseModel):
    """Respuesta agrupada por usuario y solicitud de curso."""

    user: TeacherRequestUserResponse
    courses: TeacherRequestCourseResponse
    model_config = ConfigDict(from_attributes=True)


ListTeacherAccountsResponse = list[TeacherRequestAccountResponse]


class RequestStatusUpdateSchema(BaseModel):
    """
    Payload para la transición de estados de solicitudes por parte del administrador.
    """

    institute: InstitutesEnum
    request_id: int
    new_status: RequestStatusEnum


class RequestStatusUpdateResponseSchema(BaseModel):
    """
    Modelo de respuesta tras actualizar el estado de una solicitud.
    """

    message: str
    model_config = ConfigDict(from_attributes=True)


class RequestStatusUpdateResponse(BaseModel):
    """
    Confirmación de éxito tras la actualización de estatus de una solicitud de curso.
    """

    message: str
    model_config = ConfigDict(from_attributes=True)


class CreateAccountSchema(BaseModel):
    """
    Esquema de registro final (Set Password).

    Captura el identificador de usuario y la contraseña definitiva proporcionada
    por el usuario tras validar su token de correo.
    """

    user_id: int
    new_password: str
    token: UUID4


class CreateAccountResponse(BaseModel):
    """Resultado del aprovisionamiento exitoso en Keycloak y Moodle."""

    message: str
    model_config = ConfigDict(from_attributes=True)


class CourseRequestInfo(BaseModel):
    """
    Información del curso asociado a la solicitud.
    """

    id: int
    status: RequestStatusEnum
    moodle_course_id: int | None = None  # Para alumnos
    course_full_name: str | None = None  # Para docentes
    groups: str | None = None  # Para docentes
    model_config = ConfigDict(from_attributes=True)


class UserInfoResponse(BaseModel):
    """
    Datos de contexto para la interfaz de confirmación.

    Permite al frontend mostrar al usuario sus datos registrados antes de
    completar el proceso de creación de contraseña, incluyendo la información
    del curso al que está solicitando unirse.

    El campo 'role' permite al frontend determinar qué campos de 'course_request'
    serán no-nulos:
    - ALUMNO: moodle_course_id estará poblado, course_full_name y groups serán None
    - DOCENTE: course_full_name y groups estarán poblados, moodle_course_id será None
    """

    id: int
    email: EmailStr
    name: str
    last_name: str
    role: AccountRoleEnum
    institute: InstitutesEnum
    course_request: CourseRequestInfo
    model_config = ConfigDict(from_attributes=True)
