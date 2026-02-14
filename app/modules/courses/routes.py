# Módulo APIRouter de Cursos - Proyecto MACTI
#
# Este módulo define los puntos de entrada (endpoints) para la gestión y consulta
# de la oferta académica. Centraliza las rutas relacionadas con el catálogo global
# de Moodle y la vista personalizada de cursos para usuarios autenticados,
# aplicando validaciones de esquema y filtros por instituto.

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

# Definición del router con prefijo y etiquetas para la documentación automática (Swagger)
router = APIRouter(prefix="/courses", tags=["Cursos"])


@router.get(
    "/",
    summary="Listar cursos de Moodle para un instituto específico",
    response_model=list[CourseResponseSchema],
)
async def list_courses(
    institute: InstitutesEnum = Query(..., description="Nombre del instituto (Enum)"),
) -> list[CourseResponseSchema]:
    """
    Endpoint público/administrativo para obtener el catálogo completo de Moodle.

    Permite conocer la oferta académica disponible en una instancia específica
    antes de realizar procesos de inscripción.
    """
    return await ListCoursesController.list_courses(institute=institute)


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
    """
    Endpoint privado para obtener la 'Mochila Digital' del usuario.

    Requiere un Bearer Token válido. El sistema extrae la identidad del usuario
    del token, resuelve su vinculación con Moodle y retorna sus cursos con
    el rol correspondiente (Maestro/Alumno).
    """
    return await UserEnrolledCoursesController.get_user_enrolled_courses(
        institute=institute, user_info=user_info, db=db
    )
