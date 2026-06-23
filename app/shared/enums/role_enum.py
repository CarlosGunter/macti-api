"""
Módulo de Roles de Cuenta - Proyecto MACTI

Define los roles fundamentales que un usuario puede desempeñar dentro del sistema.
Estos roles determinan los permisos de acceso, las capacidades de creación de
cursos y el flujo de aprobación que debe seguir cada solicitud.
"""

from enum import Enum


class AccountRoleEnum(str, Enum):
    """
    Enumeración de los roles de usuario permitidos.

    Hereda de 'str' para facilitar la serialización JSON y la compatibilidad
    con los tipos de datos de la base de datos (PostgreSQL/MySQL).
    """

    # Rol para usuarios que se inscriben en cursos existentes como aprendices.
    ALUMNO = "alumno"
    # Rol para usuarios con capacidad de gestionar contenidos y solicitar nuevos.
    DOCENTE = "docente"
    # Rol para usuarios con permisos completos.
    ADMIN = "admin"

    @property
    def level(self) -> int:
        """Define un nivel de jerarquía para cada rol, útil para comparaciones de permisos."""

        # De menor a mayor, más alto el número, mayor el nivel de permisos.
        _hierarchy = {
            AccountRoleEnum.ALUMNO: 1,
            AccountRoleEnum.DOCENTE: 2,
            AccountRoleEnum.ADMIN: 3,
        }

        # Asegura que todo rol tenga un nivel definido.
        if len(_hierarchy) != len(AccountRoleEnum):
            raise ValueError(
                "Todos los roles deben tener un nivel definido en la jerarquía."
            )

        return _hierarchy[self]
