from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from ..models import AccountRequest

class ListAccountRequestsController:
    @staticmethod
    def list_accounts_requests(db: Session, course_id: int):
        try:
            requests = db.query(AccountRequest).filter(
                AccountRequest.course_id == course_id
            ).all()
            return {"success": True, "data": requests}
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail="Error al obtener solicitudes")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))