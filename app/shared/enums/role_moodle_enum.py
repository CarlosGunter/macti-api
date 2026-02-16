# Módulo RoleEnum - Mapeo de Roles Estándar de Moodle
#
# Este módulo define los identificadores numéricos (IDs) de los roles nativos
# dentro de la plataforma Moodle. Es fundamental para la lógica de permisos,
# ya que permite al backend de MACTI interpretar los privilegios que un usuario
# tiene asignados dentro de un curso específico en el LMS.

from enum import Enum


class RoleEnum(int, Enum):
    """
    Enumeración de los Roles de Moodle.

    Cada miembro corresponde al ID de rol estándar configurado por defecto
    en una instalación limpia de Moodle (MDL_ROLE).
    """

    # Administrador con privilegios totales sobre el sitio o categoría.
    MANAGER = 1

    # Usuario con permisos para crear nuevos cursos.
    COURSE_CREATOR = 2

    # Docente con capacidad de editar contenidos, actividades y gestionar alumnos.
    EDITING_TEACHER = 3

    # Docente con permisos de visualización y calificación, pero sin edición de recursos.
    TEACHER = 4

    # Participante estándar inscrito para consumir contenidos y realizar actividades.
    STUDENT = 5

    # Usuario con acceso limitado de solo lectura (invitado).
    GUEST = 6

    # Usuario registrado en el sistema pero sin rol específico en el contexto del curso.
    USER = 7

    # Rol especial aplicado para la gestión de la página principal del sitio.
    FRONTPAGE = 8
