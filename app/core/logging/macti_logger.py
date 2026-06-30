"""
Funciones helper para logging estructurado en MACTI.
Cada módulo usa su propio logger_name para trazabilidad.
"""

import traceback
from typing import Any

from loguru import logger


def get_logger(name: str):
    """
    Retorna un logger con el nombre del módulo.
    Uso: logger = get_logger(__name__)
    """
    return logger.bind(logger_name=name, payload={})


def log_service_error(
    logger_name: str,
    service: str,
    endpoint: str,
    error_message: str,
    status_code: int | None = None,
    extra: dict[str, Any] | None = None,
):
    """
    Log de errores de servicios externos (Moodle, Keycloak, Jupyter).
    Se llama en servicios cuando falla una llamada a API externa.
    """
    payload = {
        "category": "service_error",
        "service": service,
        "endpoint": endpoint,
        "status_code": status_code,
        **(extra or {}),
    }
    logger.bind(logger_name=logger_name, payload=payload).error(
        f"[{service}] {endpoint} → {error_message}"
    )


def log_db_error(
    logger_name: str,
    operation: str,
    error_message: str,
    extra: dict[str, Any] | None = None,
):
    """
    Log de errores de base de datos.
    Se llama DENTRO de los try-catch en repositorios.
    """
    payload = {
        "category": "db_error",
        "operation": operation,
        "traceback": traceback.format_exc(),
        **(extra or {}),
    }
    logger.bind(logger_name=logger_name, payload=payload).error(
        f"[DB] {operation} → {error_message}"
    )


def log_macti_error(
    logger_name: str,
    error_code: str,
    message: str,
    extra: dict[str, Any] | None = None,
):
    """
    Log de errores de lógica de negocio MACTI.
    Se llama en funciones privadas de controladores.
    """
    payload = {
        "category": "macti_error",
        "error_code": error_code,
        **(extra or {}),
    }
    logger.bind(logger_name=logger_name, payload=payload).error(
        f"[MACTI] {error_code} → {message}"
    )


def log_security_event(
    logger_name: str,
    event: str,
    user_id: int | None = None,
    ip: str | None = None,
    extra: dict[str, Any] | None = None,
):
    """
    Log de eventos de seguridad (login, logout, acceso denegado, etc.).
    """
    payload = {
        "category": "security",
        "event": event,
        "user_id": user_id,
        "ip": ip,
        **(extra or {}),
    }
    logger.bind(logger_name=logger_name, payload=payload).info(
        f"[SECURITY] {event} | user_id={user_id} | ip={ip}"
    )


def log_info(
    logger_name: str,
    message: str,
    extra: dict[str, Any] | None = None,
):
    """
    Log informativo genérico.
    """
    logger.bind(logger_name=logger_name, payload=extra or {}).info(message)
