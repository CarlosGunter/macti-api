"""
Módulo AccountStatusEnum - Gestión del Ciclo de Vida de Solicitudes

Este módulo define los estados por los que atraviesa una solicitud de cuenta
en el sistema MACTI. Actúa como el controlador de flujo para las acciones
administrativas y los disparadores de servicios externos (Email, Keycloak, Moodle).
"""

from enum import Enum


class AccountStatusEnum(Enum):
    """
    Enumeración de los estados de una solicitud de cuenta.

    Cada estado representa una etapa específica en el flujo de aprobación
    y aprovisionamiento de identidad.
    """

    """Estado inicial: La solicitud ha sido registrada y espera revisión administrativa."""
    PENDING = "pending"

    """La solicitud fue revisada y aceptada; se ha enviado el correo de validación al usuario."""
    APPROVED = "approved"

    """La solicitud no cumple con los requisitos y ha sido descartada."""
    REJECTED = "rejected"

    """Paso final: El usuario validó su token y la cuenta ha sido creada en Keycloak y Moodle."""
    CREATED = "created"
