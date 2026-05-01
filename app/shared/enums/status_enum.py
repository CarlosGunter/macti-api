# Módulo AccountStatusEnum - Gestión del Ciclo de Vida de Solicitudes
#
# Este módulo define los estados por los que atraviesa una solicitud de cuenta
# en el sistema MACTI. Actúa como el controlador de flujo para las acciones
# administrativas y los disparadores de servicios externos (Email, Keycloak, Moodle).

from enum import Enum


class RequestStatusEnum(Enum):
    """
    Enumeración de los estados de una solicitud de curso.

    Cada estado representa una etapa específica en el proceso de revisión y aprobación de un curso solicitado por un docente o alumno.
    """

    # Estado inicial: La solicitud ha sido registrada y espera revisión administrativa.
    PENDING = "pending"

    # La solicitud fue revisada y aceptada por el equipo administrativo.
    APPROVED = "approved"

    # La solicitud no cumple con los requisitos y ha sido descartada.
    REJECTED = "rejected"

    # El usuario ha sido inscrito al curso solicitado.
    ENROLLED = "enrolled"
