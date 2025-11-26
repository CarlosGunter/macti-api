from fastapi import APIRouter, Query

from app.modules.courses.controllers.list_courses import ListCoursesController
from app.modules.courses.controllers.user_enrolled_courses import (
    UserEnrolledCoursesController,
)
from app.modules.courses.schemas import ListCoursesResponse
from app.shared.enums.institutes_enum import InstitutesEnum

router = APIRouter(prefix="/courses", tags=["Cursos"])


@router.get(
    "/",
    summary="Listar cursos de Moodle para un instituto específico",
    response_model=ListCoursesResponse,
)
async def list_courses(
    institute: InstitutesEnum = Query(..., description="Nombre del instituto"),
):
    return await ListCoursesController.list_courses(institute=institute)


@router.get(
    "/enrolled",
    summary="Listar cursos en los que un usuario está inscrito",
)
async def list_user_enrolled_courses(
    institute: InstitutesEnum = Query(..., description="Nombre del instituto"),
    user_id: int = Query(..., description="ID del usuario en Moodle"),
):
    return await UserEnrolledCoursesController.get_user_enrolled_courses(
        institute=institute, user_id=user_id
    )
