from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.courses.controllers.list_courses import ListCoursesController
from app.modules.courses.controllers.user_enrolled_courses import (
    UserEnrolledCoursesController,
)
from app.modules.courses.schemas import (
    CourseResponseSchema,
    UserEnrolledCoursesResponseSchema,
)
from app.shared.dependecies.get_current_user import CurrentUser, get_current_user
from app.shared.enums.institutes_enum import InstitutesEnum

router = APIRouter(prefix="/courses", tags=["Cursos"])


@router.get(
    "/",
    summary="Listar cursos de Moodle para un instituto específico",
    response_model=list[CourseResponseSchema],
)
async def list_courses(
    institute: InstitutesEnum = Query(..., description="Nombre del instituto"),
    ids: list[int] | None = Query(
        None, description="Lista de IDs de cursos para filtrar"
    ),
) -> list[CourseResponseSchema]:
    return await ListCoursesController.list_courses(institute=institute, ids=ids)


@router.get(
    "/enrolled",
    summary="Listar cursos en los que un usuario está inscrito",
    response_model=list[UserEnrolledCoursesResponseSchema],
)
async def list_user_enrolled_courses(
    institute: InstitutesEnum = Query(..., description="Nombre del instituto"),
    user_info: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[UserEnrolledCoursesResponseSchema]:
    return await UserEnrolledCoursesController.get_user_enrolled_courses(
        institute=institute, user_info=user_info, db=db
    )
