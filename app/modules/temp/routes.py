# Módulo TempRouter - Utilidades de Depuración y Pruebas
#
# Este router agrupa endpoints temporales diseñados para facilitar el ciclo de
# desarrollo. Incluye herramientas para la limpieza profunda de datos (Hard Delete),
# verificación de integridad de tokens JWT y consultas directas a servicios externos.
# Nota: Este módulo debería ser deshabilitado o protegido en entornos de producción.

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder

from app.shared.dependecies.get_current_user import get_current_user

router = APIRouter(prefix="/temp", tags=["temp"])


@router.get(
    "/bearer-test",
    summary="Endpoint de prueba para verificar el token Bearer",
)
async def bearer_test(current_user=Depends(get_current_user)):
    """
    Valida la correcta configuración del Middleware de Seguridad.

    Si el token es válido, retorna la información decodificada del usuario
    (Payload del JWT). Utiliza 'jsonable_encoder' para serializar el objeto
    de usuario actual.
    """
    return {
        "message": "Autenticación exitosa. El token Bearer es válido.",
        "user": jsonable_encoder(current_user, by_alias=False),
    }


# @router.delete(
#     "/clear-user",
#     summary="Eliminar todos los datos relacionados con un usuario específico",
# )
# async def clear_user_data(
#     user_id: int = Query(
#         ...,
#         description="ID del usuario cuyos datos serán eliminados de la BD y Keycloak",
#     ),
#     db=Depends(get_db),
# ):
#     """
#     Realiza una limpieza total de un usuario para permitir re-pruebas de registro.

#     Operaciones:
#     1. Localiza el registro en la base de datos local para obtener el contexto (Instituto).
#     2. Elimina la identidad del usuario en Keycloak (IAM).
#     3. Elimina físicamente el registro en la tabla UserAccounts.
#     """

#     # 1. Validación de existencia y obtención de contexto
#     user_data = db.query(UserAccounts).filter(UserAccounts.id == user_id).first()
#     if not user_data:
#         raise HTTPException(
#             status_code=404, detail="Usuario no encontrado en la base de datos local."
#         )

#     # 2. Eliminación en el Proveedor de Identidad (Keycloak)
#     # Es crucial eliminarlo aquí para liberar el 'username' y 'email' para nuevos registros
#     del_kc = await KeycloakService.delete_user(
#         user_id=str(user_id), institute=user_data.institute
#     )

#     # 3. Persistencia de la eliminación local
#     try:
#         db.delete(user_data)
#         db.commit()
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=500,
#             detail="Error al eliminar los registros en la base de datos.",
#         ) from e

#     if not del_kc:
#         # Si falla Keycloak pero no la BD, se notifica para limpieza manual,
#         # evitando inconsistencias de identidad.
#         raise HTTPException(
#             status_code=500,
#             detail="Datos locales borrados, pero falló la eliminación en Keycloak.",
#         )

#     return {"message": f"Usuario {user_id} eliminado exitosamente de MACTI y Keycloak."}


# @router.get(
#     "/user-moodle-info",
#     summary="Obtener información del usuario actual por su email",
# )
# async def get_user_info(
#     institute: InstitutesEnum = Query(
#         ..., description="Instituto al que pertenece el usuario"
#     ),
#     email: str = Query(..., description="Email registrado en Moodle"),
# ):
#     """
#     Consulta directa al Web Service de Moodle para depurar perfiles.

#     Permite verificar si un usuario existe en el LMS y qué datos (IDs, roles)
#     está retornando Moodle antes de integrarlos en la lógica de negocio principal.
#     """
#     return await MoodleService.get_user_profile_by_email(
#         institute=institute, user_email=email
#     )


# @router.get(
#     "/list-manager-accounts",
#     summary="Listar cuentas de administradores por instituto",
# )
# async def list_manager_accounts(
#     institute: InstitutesEnum = Query(
#         ..., description="Instituto para filtrar cuentas de administradores"
#     ),
# ):
#     """Endpoint de prueba para listar cuentas de administradores por instituto."""
#     return await RegisterMoodleService.get_admins(institute=institute)
