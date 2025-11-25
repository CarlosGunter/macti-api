import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from jose import jwt

from app.shared.config.kc_configs import keycloak_configs
from app.shared.enums.institutes_enum import InstitutesEnum

security = HTTPBearer()
ALGORITHM = "RS256"

security = HTTPBearer()
ALGORITHM = "RS256"

JWKS_CACHE: dict[InstitutesEnum, dict] = {}


async def get_jwks_for_institute(institute: InstitutesEnum) -> dict:
    if institute not in JWKS_CACHE:
        print(f"[DEBUG] JWKS para {institute.value} NO está en cache. Obteniendo...")

        kc = keycloak_configs[institute]
        url = f"{kc.url}/realms/{kc.realm}/protocol/openid-connect/certs"

        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            print(f"[DEBUG] GET {url} -> status {resp.status_code}")

            if resp.status_code != 200:
                print("[ERROR] No se pudieron obtener JWKS:", resp.text)
                raise HTTPException(
                    status_code=500,
                    detail=f"No se pudieron obtener JWKS para {institute.value}",
                )

            JWKS_CACHE[institute] = resp.json()
            print(f"[DEBUG] JWKS guardado en cache para {institute.value}")

    else:
        print(f"[DEBUG] JWKS para {institute.value} tomado de cache")

    return JWKS_CACHE[institute]


def find_signing_key(jwks: dict, kid: str) -> dict | None:
    print(f"[DEBUG] Buscando 'kid' {kid} dentro de JWKS...")

    for key in jwks.get("keys", []):
        print(f"[DEBUG] Revisando key con kid={key.get('kid')}")
        if key.get("kid") == kid:
            print("[DEBUG] Clave encontrada ✔")
            return key

    print("[ERROR] No se encontró la clave con ese kid ")
    return None


async def get_current_user(
    institute: InstitutesEnum, credentials=Depends(security)
) -> dict:
    token = credentials.credentials
    print(f"[DEBUG] Token recibido (primeros 40 chars): {token[:40]}...")
    jwks = await get_jwks_for_institute(institute)
    try:
        unverified_header = jwt.get_unverified_header(token)
        print(f"[DEBUG] Encabezado del token: {unverified_header}")

        kid = unverified_header.get("kid")
        print(f"[DEBUG] kid extraído: {kid}")

        if not kid:
            print("[ERROR] Token no contiene KID")
            raise HTTPException(status_code=401, detail="Token header missing 'kid'")
    except Exception as e:
        print("[ERROR] Error leyendo encabezado del token:", str(e))
        raise HTTPException(status_code=401, detail="Invalid token header") from e

    signing_key = find_signing_key(jwks, kid)
    if not signing_key:
        raise HTTPException(status_code=401, detail="Invalid signing key")

    kc = keycloak_configs[institute]
    issuer = f"{kc.url}/realms/{kc.realm}"

    print(f"[DEBUG] Intentando decodificar token con issuer: {issuer}")
    print(f"[DEBUG] Usando key type={signing_key.get('kty')} alg={ALGORITHM}")

    try:
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=[ALGORITHM],
            audience="account",
            issuer=issuer,
        )

        print("[DEBUG] Token decodificado correctamente ✔")
        print(f"[DEBUG] Payload recibido: {payload}")
        azp = payload.get("azp")
        print(f"[DEBUG] azp: {azp} (debe coincidir con {kc.client_id})")

        if azp != kc.client_id:
            print("[ERROR] azp inválido")
            raise HTTPException(status_code=401, detail="Invalid azp (client) in token")

    # Si te marca algun error solo descomente los type o bórralos
    except jwt.ExpiredSignatureError:  # type: ignore
        print("[ERROR] Token expirado ")
        raise HTTPException(status_code=401, detail="Token expired") from None

    except jwt.JWTError as e:  # type: ignore
        print("[ERROR] Error verificando token:", str(e))
        raise HTTPException(status_code=401, detail="Invalid token") from e

    print("[DEBUG] Usuario autenticado correctamente")
    return payload
