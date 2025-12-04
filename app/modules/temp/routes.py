from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder

from app.core.database import get_db
from app.modules.auth.models import AccountRequest
from app.modules.auth.services.kc_service import KeycloakService
from app.shared.dependecies.get_current_user import get_current_user
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.services.moodle_service import MoodleService

router = APIRouter(prefix="/temp", tags=["temp"])


@router.delete(
    "/clear-user",
    summary="Eliminar todos los datos relacionados con un usuario específico",
)
async def clear_user_data(
    user_id: int = Query(
        ..., description="ID del usuario cuyos datos serán eliminados"
    ),
    db=Depends(get_db),
):
    user_data = db.query(AccountRequest).filter(AccountRequest.id == user_id).first()
    if not user_data:
        raise HTTPException(
            status_code=404, detail="Usuario no encontrado en la base de datos."
        )

    del_kc = await KeycloakService.delete_user(
        user_id=str(user_id), institute=user_data.institute
    )

    try:
        db.delete(user_data)
        db.commit()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Error al eliminar los datos del usuario en la BD."
        ) from e

    if not del_kc:
        raise HTTPException(
            status_code=500, detail="Error al eliminar el usuario en Keycloak."
        )

    return {
        "message": f"Datos del usuario con ID {user_id} eliminados correctamente de la BD y KC."
    }


@router.get(
    "/bearer-test",
    summary="Endpoint de prueba para verificar el token Bearer",
)
async def bearer_test(current_user=Depends(get_current_user)):
    return {
        "message": "Token Bearer válido. Acceso concedido al endpoint de prueba.",
        "user": jsonable_encoder(current_user, by_alias=False),
    }


@router.get(
    "/user-moodle-info",
    summary="Obtener información del usuario actual por su email",
)
async def get_user_info(
    institute: InstitutesEnum = Query(..., description="Instituto del usuario"),
    email: str = Query(..., description="Email del usuario"),
):
    return await MoodleService.get_user_profile_by_email(
        institute=institute, user_email=email
    )
