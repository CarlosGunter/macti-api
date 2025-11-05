from fastapi import HTTPException
from sqlalchemy import String, cast, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..models import AccountRequest


class ListAccountRequestsController:
    @staticmethod
    def list_accounts_requests(db: Session, course_id: int):
        try:
            # Hacer una selección explícita y usar mappings() para obtener dicts
            stmt = select(
                AccountRequest.id,
                AccountRequest.name,
                AccountRequest.last_name,
                AccountRequest.email,
                cast(AccountRequest.status, String).label("status"),
            ).where(AccountRequest.course_id == course_id)

            result = db.execute(stmt)
            rows = result.mappings().all()

            # Para que coincida exactamente con el response_model
            return [dict(r) for r in rows]

        except SQLAlchemyError:
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "DB_ERROR",
                    "message": "Error al obtener solicitudes",
                },
            ) from SQLAlchemyError

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail={"error_code": "ERROR_DESCONOCIDO", "message": str(e)},
            ) from e
