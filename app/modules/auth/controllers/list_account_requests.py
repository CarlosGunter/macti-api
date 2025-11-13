from fastapi import HTTPException
from sqlalchemy import case, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..models import AccountRequest, AccountStatusEnum, InstituteEnum


class ListAccountRequestsController:
    @staticmethod
    def list_accounts_requests(
        db: Session,
        course_id: int,
        institute: InstituteEnum,
        status: AccountStatusEnum | None = None,
    ):
        try:
            # Hacer una selección explícita y usar mappings() para obtener dicts
            status_order = case(
                (AccountRequest.status == AccountStatusEnum.pending, 0),
                (AccountRequest.status == AccountStatusEnum.approved, 1),
                (AccountRequest.status == AccountStatusEnum.rejected, 2),
                (AccountRequest.status == AccountStatusEnum.created, 3),
                else_=4,
            )

            filters = [
                AccountRequest.course_id == course_id,
                AccountRequest.institute == institute,
            ]

            if status is not None:
                filters.append(AccountRequest.status == status)

            stmt = (
                select(
                    AccountRequest.id,
                    AccountRequest.name,
                    AccountRequest.last_name,
                    AccountRequest.email,
                    AccountRequest.status,
                )
                .where(*filters)
                .order_by(status_order, AccountRequest.status)
            )

            result = db.execute(stmt)
            rows = result.mappings().all()

            # Para que coincida exactamente con el response_model
            return [dict(r) for r in rows]

        except SQLAlchemyError as exc:
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "DB_ERROR",
                    "message": "Error al obtener solicitudes",
                },
            ) from exc

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail={"error_code": "ERROR_DESCONOCIDO", "message": str(e)},
            ) from e
