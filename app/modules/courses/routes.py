from fastapi import APIRouter, Depends, Query

from app.core.database import get_db
from app.modules.courses.controllers.list_courses import ListCoursesController
from app.modules.courses.controllers.user_enrolled_courses import (
    UserEnrolledCoursesController,
)
from app.modules.courses.schemas import (
    ListCoursesResponse,
    UserEnrolledCoursesResponse,
)
from app.shared.dependecies.get_current_user import get_current_user
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
    response_model=UserEnrolledCoursesResponse,
    dependencies=[Depends(get_current_user), Depends(get_db)],
)
async def list_user_enrolled_courses(
    institute: InstitutesEnum = Query(..., description="Nombre del instituto"),
    user_info: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return await UserEnrolledCoursesController.get_user_enrolled_courses(
        institute=institute, user_info=user_info, db=db
    )
