"""
Repositorio para operaciones de BD necesarias por UserEnrolledCoursesController.
Encapsula la resolución de `JIDs` por `kc_id` y asegura `joinedload` de relaciones usadas.
"""

from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.shared.models.auth_model import Auth
from app.shared.models.jids_model import JIDs


class UserEnrolledCoursesRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_jids_by_kc_id(self, kc_id: UUID) -> list[JIDs]:
        """Devuelve todas las filas de JIDs que coincidan con `kc_id`.

        Carga la relación `auth` y `auth.profile` para evitar lazy-loading
        en capas superiores que consumen esos campos.
        """
        return (
            self.db.query(JIDs)
            .options(joinedload(JIDs.auth).joinedload(Auth.profile))
            .filter(JIDs.kc_id == kc_id)
            .all()
        )
