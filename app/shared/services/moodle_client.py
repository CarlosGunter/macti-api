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
    Realiza una petición HTTP a Moodle con manejo de errores legible.

    Args:
        url: URL del endpoint de Moodle
        method: Método HTTP ('GET', 'POST', etc.)
        params: Parámetros de query string
        data: Datos para el body (form-encoded)
        json: Datos JSON para el body
        institute: Instituto para contexto en errores
        timeout: Timeout en segundos
        check_moodle_errors: Si verificar errores específicos de Moodle en la respuesta

    Returns:
        Dict con:
        - success: bool indicando si la petición fue exitosa
        - data: dict con la respuesta JSON si success=True, None si no
        - error_message: str con mensaje de error si success=False, None si success=True
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method=method, url=url, params=params, data=data, json=json
            )
            response.raise_for_status()
            response_data = response.json()

        # Verificar errores específicos de Moodle en la respuesta si está habilitado
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
        institute_str = f" ({institute})" if institute else ""
        return {
            "success": False,
            "data": None,
            "error_message": f"Error HTTP en Moodle{institute_str}: {e.response.status_code} - {e.response.text}",
        }
    except httpx.TimeoutException:
        institute_str = f" ({institute})" if institute else ""
        return {
            "success": False,
            "data": None,
            "error_message": f"Timeout conectando a Moodle{institute_str}",
        }
    except httpx.RequestError as e:
        institute_str = f" ({institute})" if institute else ""
        return {
            "success": False,
            "data": None,
            "error_message": f"Error de conexión con Moodle{institute_str}: {str(e)}",
        }
    except Exception as e:
        institute_str = f" ({institute})" if institute else ""
        return {
            "success": False,
            "data": None,
            "error_message": f"Error inesperado en Moodle{institute_str}: {str(e)}",
        }
