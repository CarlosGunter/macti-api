from fastapi import APIRouter, Query

from app.modules.courses.controllers.list_courses import ListCoursesController
from app.shared.enums.institutes_enum import InstitutesEnum

router = APIRouter(prefix="/courses", tags=["Cursos"])


@router.get("/", summary="Listar cursos de Moodle para un instituto específico")
async def list_courses(
    institute: InstitutesEnum = Query(..., description="Nombre del instituto"),
):
    return await ListCoursesController.list_courses(institute=institute)
