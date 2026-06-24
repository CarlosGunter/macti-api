import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.nbgrader.controllers.sync_grade_controller import sync_grade_controller
from app.modules.nbgrader.controllers.sync_students_controller import (
    sync_students_controller,
)
from app.modules.nbgrader.schemas import GradeSyncResponse, GradeSyncSchema

# Importamos tu servicio y el modelo/dependencia de la base de datos
from app.modules.nbgrader.services.jupyter_service import JupyterService

# NOTA: Ajusta el import de la DB si tus compañeros renombraron la dependencia para obtener la sesión
from app.shared.models.auth_model import Auth

router = APIRouter(prefix="/jupyter", tags=["JupyterHub / nbgrader"])

logger = logging.getLogger(__name__)

sync_router = APIRouter(tags=["JupyterHub / nbgrader Sincronización"])


@router.post(
    "/sync-grade",
    response_model=GradeSyncResponse,
    summary="Sincronizar calificación desde nbgrader",
    description="Busca un curso y tarea en Moodle (en un instituto específico o en todos) y actualiza la calificación del alumno de forma automática.",
)
async def sync_grade(data: GradeSyncSchema):
    return await sync_grade_controller(data)


@router.get("/user/{email}", response_model=dict[str, Any])
async def get_jupyter_user_info(email: str):
    """Consulta el estado, grupos y conectividad real de un usuario directamente en JupyterHub."""
    result = await JupyterService.get_user_info(username=email)

    if "error" in result:
        raise HTTPException(
            status_code=404,
            detail={"error_code": "JUPYTER_USER_NOT_FOUND", "message": result["error"]},
        )
    return result


@router.get("/users/status-summary", response_model=list[dict[str, Any]])
async def get_all_users_jupyter_status(
    # Reemplazamos el lambda por la dependencia real del proyecto
    db: Session = Depends(get_db),
):
    """Genera un reporte cruzado: extrae los usuarios de la base de datos de MACTI

    y consulta sus grupos y permisos administrativos vigentes en JupyterHub.
    """
    try:
        # 1. Recuperamos los usuarios registrados en el sistema desde la tabla Auth
        # (Ajusta la consulta si tus compañeros cambiaron el modelo de usuarios principal)
        db_users = db.query(Auth).all()

        if not db_users:
            return []

        # 2. Mandamos la lista a tu JupyterService para el barrido de la API
        summary = await JupyterService.get_all_users_status(db_users=db_users)
        return summary

    except Exception as err:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "SUMMARY_GENERATION_FAILED",
                "message": f"Error interno al generar el reporte cruzado: {str(err)}",
            },
        )


@router.post("/force-sync-user", tags=["JupyterHub / nbgrader"])
async def force_sync_user_to_jupyter(email: str, role: str = "docente"):
    """
    Endpoint de emergencia para forzar el alta e inscripción
    de cualquier correo directamente en JupyterHub.
    """
    try:
        # Forzamos la ejecución de tu servicio con el json={} que ya reparamos
        success = await JupyterService.sync_user_role(email=email, role=role)
        if success:
            return {
                "status": "success",
                "message": f"Usuario {email} sincronizado correctamente en el Hub",
            }
        else:
            return {
                "status": "error",
                "message": "JupyterHub rechazó la petición. Revisa el Token.",
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@sync_router.get("/nbgrader/sync-students")
async def sync_students_hub(teacher_email: str, db: Session = Depends(get_db)):
    return await sync_students_controller(teacher_email, db)
