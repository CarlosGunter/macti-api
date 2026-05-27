from fastapi import APIRouter

from app.modules.nbgrader.controllers.sync_grade_controller import sync_grade_controller
from app.modules.nbgrader.schemas import GradeSyncResponse, GradeSyncSchema

router = APIRouter(prefix="/nbgrader", tags=["nbgrader"])


@router.post(
    "/sync-grade",
    response_model=GradeSyncResponse,
    summary="Sincronizar calificación desde nbgrader",
    description="Busca un curso y tarea en Moodle (en un instituto específico o en todos) y actualiza la calificación del alumno de forma automática.",
)
async def sync_grade(data: GradeSyncSchema):
    return await sync_grade_controller(data)
