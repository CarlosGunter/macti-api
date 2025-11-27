import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError, JWTError

from app.shared.config.kc_configs import keycloak_configs
from app.shared.enums.institutes_enum import InstitutesEnum

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
                    detail={
                        "error_code": "KC_JWKS_ERROR",
                        "message": f"No se pudieron obtener JWKS para {institute.value}",
                    },
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
            raise HTTPException(
                status_code=401,
                detail={
                    "error_code": "FALTA_KID_TOKEN",
                    "message": "Falta 'kid' en el encabezado del token",
                },
            )
    except Exception as e:
        print("[ERROR] Error leyendo encabezado del token:", str(e))
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": "ENCABEZADO_TOKEN_INVALIDO",
                "message": "Encabezado del token inválido",
            },
        ) from e

    signing_key = find_signing_key(jwks, kid)
    if not signing_key:
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": "CLAVE_FIRMA_INVALIDA",
                "message": "Clave de firma inválida",
            },
        )

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
        print(f"[DEBUG] azp: {azp} (debe coincidir con el cliente del frontend)")

        if azp != "next-login":
            print("[ERROR] azp inválido")
            raise HTTPException(
                status_code=401,
                detail={
                    "error_code": "CLIENTE_INVALIDO",
                    "message": "Cliente (azp) inválido en el token",
                },
            )

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail={"error_code": "TOKEN_EXPIRADO", "message": "Token expirado"},
        ) from ExpiredSignatureError

    except JWTClaimsError:
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": "RECLAMACIONES_TOKEN_INVALIDAS",
                "message": "Reclamaciones del token inválidas",
            },
        ) from JWTClaimsError

    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail={"error_code": "FIRMA_TOKEN_INVALIDA", "message": "Token inválido"},
        ) from e

    print("[DEBUG] Usuario autenticado correctamente")
    return payload
