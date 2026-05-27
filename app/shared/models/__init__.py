"""Importa todos los modelos para registrarlos en el metadata de SQLAlchemy."""

from app.shared.models.auth_model import Auth
from app.shared.models.JIDs_model import JIDs
from app.shared.models.student_courses_model import StudentCourseRequest
from app.shared.models.teacher_courses_model import TeacherCourseRequest
from app.shared.models.user_profiles_model import UserProfile
from app.shared.models.verification_tokens_model import VerificationToken

__all__ = [
    "Auth",
    "JIDs",
    "StudentCourseRequest",
    "TeacherCourseRequest",
    "UserProfile",
    "VerificationToken",
]
