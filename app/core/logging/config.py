# app/core/logging/config.py
"""
Configuración centralizada de logging para MACTI API.
Utiliza loguru con sinks a archivos JSON rotativos diarios y stderr para k8s.
Los logs se almacenan en app/core/logging/logs/ dentro del proyecto.
En producción, montar un PersistentVolume en esta ruta.
"""

import sys
from pathlib import Path

from loguru import logger

# Ruta dentro del proyecto
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Formato JSON para parseo automático por Fluentd/Logstash
JSON_FORMAT = (
    "{{"
    '"timestamp": "{time:YYYY-MM-DD HH:mm:ss.SSSSSS}",'
    '"level": "{level}",'
    '"logger": "{extra[logger_name]}",'
    '"file": "{name}",'
    '"line": {line},'
    '"function": "{function}",'
    '"message": "{message}",'
    '"extra": {extra[payload]}'
    "}}"
)

# Formato stderr más simple, no requiere logger_name
STDERR_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{extra[logger_name]}</cyan> | "
    "<level>{message}</level>"
)


def setup_logging():
    """Configura los sinks de loguru. Se llama una vez al arrancar la app."""

    # Remover sink por defecto
    logger.remove()

    # 1. Sink a stderr (para kubectl logs / terminal)
    logger.add(
        sys.stderr,
        format=STDERR_FORMAT,
        level="DEBUG",
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # 2. Sink de errores: un archivo por día, JSON, 30 días de retención
    logger.add(
        LOG_DIR / "error_{time:YYYY-MM-DD}.jsonl",
        format=JSON_FORMAT,
        level="ERROR",
        rotation="00:00",
        retention="30 days",
        compression="gz",
        enqueue=True,
        backtrace=True,
        diagnose=True,
        filter=lambda record: record["level"].name == "ERROR",
    )

    # 3. Sink de aplicación: info, seguridad, auditoría
    logger.add(
        LOG_DIR / "app_{time:YYYY-MM-DD}.jsonl",
        format=JSON_FORMAT,
        level="INFO",
        rotation="00:00",
        retention="30 days",
        compression="gz",
        enqueue=True,
        backtrace=True,
        diagnose=False,
    )

    # 4. Sink crítico separado para alertas
    logger.add(
        LOG_DIR / "critical_{time:YYYY-MM-DD}.jsonl",
        format=JSON_FORMAT,
        level="CRITICAL",
        rotation="00:00",
        retention="90 days",
        compression="gz",
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    # Usar logger.bind para este primer mensaje
    logger.bind(logger_name="macti.logging", payload={}).info(
        "Logging configurado correctamente"
    )
