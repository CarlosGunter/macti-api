# Módulo de Esquemas Pydantic - Proyecto MACTI
#
# Este módulo define las estructuras de datos (Modelos de Validación) para la
# comunicación entre el Front-end y el Backend. Utiliza Pydantic para asegurar
# que los datos de entrada cumplan con los tipos requeridos y para formatear
# las respuestas JSON de salida de manera consistente.

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.enums.status_enum import AccountStatusEnum


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
    course_id: int | None = Field(
        None,
        ge=0,
        description="ID opcional. Si se omite, se procesa como creación de curso nuevo.",
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
    status: AccountStatusEnum
    model_config = ConfigDict(from_attributes=True)


ListAccountsResponse = list[AccountsResponse]


class ConfirmAccountSchema(BaseModel):
    """
    Payload para la transición de estados por parte del administrador.

    Recibe el ID de la solicitud y el nuevo estado definido por el Enum 'AccountStatusEnum'.
    """

    id: int
    status: AccountStatusEnum


class ConfirmAccountResponse(BaseModel):
    """Confirmación de éxito tras la actualización de estatus de una cuenta."""

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


class CreateAccountResponse(BaseModel):
    """Resultado del aprovisionamiento exitoso en Keycloak y Moodle."""

    message: str
    model_config = ConfigDict(from_attributes=True)


class UserInfoResponse(BaseModel):
    """
    Datos de contexto para la interfaz de confirmación.

    Permite al frontend mostrar al usuario sus datos registrados antes de
    completar el proceso de creación de contraseña.
    """

    id: int
    email: EmailStr
    name: str
    last_name: str
    institute: InstitutesEnum
    model_config = ConfigDict(from_attributes=True)
