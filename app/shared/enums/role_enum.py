# Módulo de Roles de Cuenta - Proyecto MACTI
#
# Define los roles fundamentales que un usuario puede desempeñar dentro del sistema.
# Estos roles determinan los permisos de acceso, las capacidades de creación de
# cursos y el flujo de aprobación que debe seguir cada solicitud.

from enum import Enum


class AccountRoleEnum(str, Enum):
    """
    Enumeración de los roles de usuario permitidos.

    Hereda de 'str' para facilitar la serialización JSON y la compatibilidad
    con los tipos de datos de la base de datos (PostgreSQL/MySQL).
    """

    # Rol para usuarios que se inscriben en cursos existentes como aprendices.
    ALUMNO = "alumno"

    # Rol para usuarios con capacidad de gestionar contenidos y solicitar nuevos espacios académicos.
    DOCENTE = "docente"
