import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.modules.auth.models import MCT_Validacion, AccountRequest, AccountStatusEnum
from app.modules.auth.controllers import AuthController
from app.modules.auth.services.kc_service import KeycloakService
from app.modules.auth.services.email_service import EmailService

TEST_EMAIL = "hola@correo.com"
NEW_PASSWORD = "correpruebas!1"

def simulate_add_request(db: Session, email: str):
    account_request = db.query(AccountRequest).filter(AccountRequest.email == email).first()
    if not account_request:
        account_request = AccountRequest(
            name="Usuario",
            last_name="Prueba",
            email=email,
            course_id=1,
            status=AccountStatusEnum.pending
        )
        db.add(account_request)
        db.commit()
        db.refresh(account_request)
        print(f"Solicitud creada para {email}")
    return account_request

async def ensure_user_in_keycloak(email):
    user_data = {
        "email": email,
        "name": "Usuario",
        "last_name": "Prueba",
        "password": "temporal123"
    }
    result = await KeycloakService.create_user(user_data)
    if result.get("created"):
        print(f"Usuario creado en Keycloak: {email}")
        return result.get("user_id")
    else:
        user = await KeycloakService.get_user_by_email(email)
        print(f"Usuario ya existía en Keycloak: {email}")
        return user.get("id")

async def simulate_profesor_approves(db: Session, email: str):
    account_request = db.query(AccountRequest).filter(AccountRequest.email == email).first()
    account_request.status = "approved"
    db.commit()
    db.refresh(account_request)

    account_request.kc_id = await ensure_user_in_keycloak(email)
    db.commit()
    db.refresh(account_request)
    token_data = EmailService.generate_and_save_token(email)
    print(f"Token generado para {email}: {token_data.get('token')}")
    return token_data.get("token")

async def complete_account_flow(db: Session, token: str, new_password: str):
    result = await AuthController.complete_account(token=token, new_password=new_password, db=db)
    print("Resultado de complete_account:", result)

async def test_complete_flow():
    db = SessionLocal()
    try:
  
        simulate_add_request(db, TEST_EMAIL)

        
        token = await simulate_profesor_approves(db, TEST_EMAIL)

        
        await complete_account_flow(db, token, NEW_PASSWORD)

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_complete_flow())
