from sqlalchemy.orm import Session

from app.modules.auth.models import AccountRequest, AccountStatusEnum
from app.modules.auth.services.email_service import EmailService
from app.modules.auth.services.kc_service import KeycloakService

TEST_EMAIL = "hola@correo.com"
NEW_PASSWORD = "correpruebas!1"  # noqa: S105


def simulate_add_request(db: Session, email: str):
    account_request = (
        db.query(AccountRequest).filter(AccountRequest.email == email).first()
    )
    if not account_request:
        account_request = AccountRequest(
            name="Usuario",
            last_name="Prueba",
            email=email,
            course_id=1,
            status=AccountStatusEnum.pending,
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
        "password": "temporal123",
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
    account_request = (
        db.query(AccountRequest).filter(AccountRequest.email == email).first()
    )
    if not account_request:
        raise Exception(f"No existe la solicitud para {email}")
    account_request.status = AccountStatusEnum.approved
    db.commit()
    db.refresh(account_request)

    account_request.kc_id = await ensure_user_in_keycloak(email)
    db.commit()
    db.refresh(account_request)
    token_data = EmailService.generate_and_save_token(email)
    print(f"Token generado para {email}: {token_data.get('token')}")
    return token_data.get("token")
