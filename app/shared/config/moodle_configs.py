# Módulo de Configuración de Moodle LMS - Proyecto MACTI
#
# Este módulo gestiona la conectividad con las diversas instancias de Moodle
# utilizadas por los institutos. Define un catálogo centralizado que mapea cada
# instituto con su respectivo punto de enlace (endpoint) de Web Services y su
# token de autenticación REST.

from dataclasses import dataclass

from app.core.environment import environment

from ..enums.institutes_enum import InstitutesEnum


@dataclass
class DCMoodleConfig:
    """
    Data Transfer Object (DTO) para los parámetros de conexión de Moodle.

    Atributos:
        moodle_url: URL del servidor de Moodle que apunta al script de Web Services.
        moodle_token: Token de seguridad (WSToken) generado en Moodle para acceso externo.
    """

    moodle_url: str
    moodle_token: str
    admins: list[str] | None = (
        None  # Lista opcional de correos electrónicos de administradores
    )


# Diccionario Maestro de Configuraciones de Moodle (LMS).
#
# Permite que el sistema MACTI sea agnóstico respecto a la ubicación física de
# los servidores de Moodle. Al recibir un 'institute', el servicio de Moodle
# conecta dinámicamente con la IP y el puerto correspondientes, permitiendo una
# administración multi-instancia desde un solo backend.


MOODLE_CONFIG: dict[InstitutesEnum, DCMoodleConfig] = {
    InstitutesEnum.PRINCIPAL: DCMoodleConfig(
        moodle_url="https://tlapoa.lamod.unam.mx/lmsier/webservice/rest/server.php",
        moodle_token=environment.MOODLE_TOKEN_PRINCIPAL,
    ),
}
