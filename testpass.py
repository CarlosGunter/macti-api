# pip install pytest
#https://pypi.org/project/pytest/
# pip install pytest-asyncio
#python -m pytest -v .\testpass.py
#https://pypi.org/project/pytest-asyncio/
import pytest
import asyncio
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.modules.auth.models import AccountRequest, AccountStatusEnum, MCT_Validacion
from app.modules.auth.services.kc_service import KeycloakService

TEST_EMAIL = "the.captain312@gmail.com"
NEW_PASSWORD = "holaCharles"

@pytest.mark.asyncio
async def test_change_password_and_update_status():
    db: Session = SessionLocal()
    try:
        account_request = db.query(AccountRequest).filter(AccountRequest.email == TEST_EMAIL).first()
        assert account_request is not None, "No se encontró la solicitud de cuenta"
        assert account_request.status == AccountStatusEnum.approved, "La cuenta no está en estado approved"
        keycloak_result = await KeycloakService.update_user_password(account_request.kc_id, NEW_PASSWORD)
        assert keycloak_result.get("success"), f"Error cambiando contraseña: {keycloak_result.get('error')}"
        account_request.status = AccountStatusEnum.created
        db.commit()
        db.refresh(account_request)
        assert account_request.status == AccountStatusEnum.created, "No se actualizó el estado a 'created'"
        token_entry = db.query(MCT_Validacion).filter(MCT_Validacion.email == TEST_EMAIL).first()
        if token_entry:
            db.delete(token_entry)
            db.commit()
        token_entry_check = db.query(MCT_Validacion).filter(MCT_Validacion.email == TEST_EMAIL).first()
        assert token_entry_check is None, "No se eliminó el token de MCT_Validacion"

    finally:
        db.close()
