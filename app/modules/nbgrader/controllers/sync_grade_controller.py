from fastapi import HTTPException

from app.modules.nbgrader.schemas import GradeSyncSchema
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.services.moodle_service import MoodleService


async def sync_grade_controller(data: GradeSyncSchema):
    target_institute = data.institute
    m_courseid = None

    if target_institute is None:
        for inst in InstitutesEnum:
            try:
                m_courseid = await MoodleService.get_course_by_shortname(
                    data.course_shortname, inst
                )
                if m_courseid:
                    target_institute = inst
                    break
            except Exception:  # noqa: S112
                continue

    else:
        m_courseid = await MoodleService.get_course_by_shortname(
            data.course_shortname, target_institute
        )

    if not target_institute or not m_courseid:
        raise HTTPException(
            status_code=404, detail=f"Curso '{data.course_shortname}' no encontrado"
        )

    m_userid = await MoodleService.get_user_by_email(data.email, target_institute)
    if not m_userid:
        raise HTTPException(
            status_code=404, detail=f"Usuario '{data.email}' no encontrado"
        )

    m_assignid = await MoodleService.get_assignment_id_by_name(
        m_courseid, data.assignment_name, target_institute
    )
    if not m_assignid:
        raise HTTPException(
            status_code=404, detail=f"Tarea '{data.assignment_name}' no encontrada"
        )

    result = await MoodleService.update_grade(
        institute=target_institute,
        course_id=m_courseid,
        assignment_id=m_assignid,
        moodle_userid=m_userid,
        grade=data.score,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error_message", "Error al actualizar nota"),
        )

    return {
        "message": "Calificación sincronizada con éxito",
        "institute_found": target_institute.value,
        "details": result.get("data"),
    }
