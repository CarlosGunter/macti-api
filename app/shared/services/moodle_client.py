# Módulo MoodleClient - Cliente HTTP Asíncrono Especializado
#
# Este módulo proporciona una capa de abstracción sobre httpx para interactuar
# con la API de Moodle. Su principal ventaja es el manejo robusto de excepciones
# específicas del protocolo de Web Services de Moodle, transformando respuestas
# inconsistentes en un formato de resultado estandarizado (success/data/error).

import httpx

from app.shared.enums.institutes_enum import InstitutesEnum


async def make_moodle_request(
    url: str,
    method: str = "POST",
    params: dict | None = None,
    data: dict | None = None,
    json: dict | None = None,
    institute: InstitutesEnum | None = None,
    timeout: float = 30.0,
    *,
    check_moodle_errors: bool = True,
) -> dict:
    """
    Realiza una petición HTTP a Moodle con gestión de errores centralizada.

    Lógica de validación:
    1. Ejecuta la petición asíncrona mediante httpx.
    2. Valida errores de protocolo HTTP (4xx, 5xx).
    3. Analiza el cuerpo JSON en busca de la clave 'exception', la cual Moodle
        usa para reportar errores lógicos incluso en respuestas exitosas (200 OK).

    Returns:
        Dict: Contiene 'success' (bool), 'data' (respuesta útil) y 'error_message'.
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method=method, url=url, params=params, data=data, json=json
            )
            response.raise_for_status()
            response_data = response.json()

        # Validación de 'Lógica Moodle': Detecta fallos internos del LMS
        if (
            check_moodle_errors
            and isinstance(response_data, dict)
            and "exception" in response_data
        ):
            return {
                "success": False,
                "data": None,
                "error_message": f"Error en la API de Moodle: {response_data.get('message', 'Error desconocido')}",
            }

        return {"success": True, "data": response_data, "error_message": None}

    except httpx.HTTPStatusError as e:
        institute_str = f" ({institute.value})" if institute else ""
        return {
            "success": False,
            "data": None,
            "error_message": f"Error HTTP en Moodle{institute_str}: {e.response.status_code}",
        }
    except httpx.TimeoutException:
        institute_str = f" ({institute.value})" if institute else ""
        return {
            "success": False,
            "data": None,
            "error_message": f"Timeout conectando a Moodle{institute_str}",
        }
    except httpx.RequestError as e:
        institute_str = f" ({institute.value})" if institute else ""
        return {
            "success": False,
            "data": None,
            "error_message": f"Error de conexión con Moodle{institute_str}: {str(e)}",
        }
    except Exception as e:
        institute_str = f" ({institute.value})" if institute else ""
        return {
            "success": False,
            "data": None,
            "error_message": f"Error inesperado en Moodle{institute_str}: {str(e)}",
        }
