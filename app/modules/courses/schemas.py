# Módulo de Esquemas de Cursos - Proyecto MACTI
#
# Define las estructuras de datos para la serialización de respuestas
# relacionadas con la oferta académica. Estos esquemas aseguran que el
# Front-end reciba únicamente los campos necesarios y validados provenientes
# de las APIs externas de Moodle.

from pydantic import BaseModel


class CourseResponseSchema(BaseModel):
    """
    Representación estandarizada de un curso de Moodle.

    Contiene la información básica para mostrar en catálogos o listas
    generales de la plataforma.
    """

    id: int
    shortname: str
    fullname: str
    displayname: str
    summary: str

    # URL de la imagen representativa del curso, puede ser nula si no se ha configurado.
    courseimage: str | None = None


class UserEnrolledCoursesResponseSchema(CourseResponseSchema):
    """
    Extensión del esquema de curso para perfiles de usuario.

    Añade el atributo 'role', que especifica los permisos o niveles de
    acceso que el usuario autenticado posee dentro de este curso específico.
    """

    # Lista de nombres de roles (ej. ['student'], ['editingteacher']).
    role: list[str] | None = None
