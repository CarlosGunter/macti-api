from fastapi import APIRouter, Depends, Query

from app.core.database import get_db
from .schema import AccountRequestSchema, ConfirmAccountSchema, CreateAccountSchema
from .controllers import AuthController
from typing import List

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/request-account", response_model=AccountRequestSchema)
async def request_account(
    data: AccountRequestSchema,
    controller: AuthController = Depends(),
    db=Depends(get_db)
):
    return controller.request_account(data=data, db=db)

@router.get("/list-accounts-requests", response_model=List[AccountRequestSchema])
async def list_accounts_requests(
    course_id: int = Query(description="Filter by course ID"),
    controller: AuthController = Depends(),
    db=Depends(get_db)
):
    return controller.list_accounts_requests(
        db=db,
        course_id=course_id
    )

@router.patch("/confirm-account", response_model=ConfirmAccountSchema)
async def confirm_account(
    data: ConfirmAccountSchema,
    controller: AuthController = Depends(),
    db=Depends(get_db)
):
    return controller.confirm_account(data, db=db)

@router.post("/create-account", response_model=CreateAccountSchema)
async def create_account(
    post: CreateAccountSchema,
    controller: AuthController = Depends(),
    db=Depends(get_db)
):
    return controller.create_account(post=post, db=db)
